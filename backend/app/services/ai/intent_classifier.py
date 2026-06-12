"""Intent classifier: LLM Call #1 with dual-layer fallback."""
import asyncio
import logging
from openai import AsyncOpenAI
from pydantic import ValidationError
from app.core.config import settings
from app.schemas.auth import UserContext
from app.schemas.intent import IntentResult
from app.services.ai.schema_index import SchemaIndexService
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.intent_definitions import get_intent_enum_values
from app.services.ai.clarification import ClarificationService

logger = logging.getLogger(__name__)


def _build_json_schema() -> dict:
    """Build the JSON Schema for strict structured output mode."""
    return {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": get_intent_enum_values()},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "complexity": {"type": "string", "enum": ["simple", "moderate", "complex"]},
            "slots": {
                "type": "object",
                "properties": {
                    "time_range": {"type": "object"},
                    "scope_type": {"type": "string"},
                    "scope_name": {"type": ["string", "null"]},
                    "course_name": {"type": ["string", "null"]},
                    "exam_name": {"type": ["string", "null"]},
                    "metric": {"type": ["string", "null"]},
                    "compare_with_previous": {"type": "boolean"},
                    "top_n": {"type": "integer", "minimum": 1, "maximum": 100},
                    "granularity": {"type": "string"},
                },
                "required": ["time_range", "scope_type"],
            },
            "need_clarification": {"type": "boolean"},
            "clarification_question": {"type": ["string", "null"]},
        },
        "required": ["intent", "confidence", "complexity", "slots", "need_clarification"],
        "additionalProperties": False,
    }


INTENT_JSON_SCHEMA = _build_json_schema()


class ClassificationError(Exception):
    """Intent classification failed at all layers."""


class IntentClassifier:
    """Classify user questions into structured intent + slots.

    Uses dual-layer LLM calling strategy:
    1. Primary: json_schema strict mode (enforces schema at API level)
    2. Fallback: json_object mode (compatible with any OpenAI-compatible API)
    """

    def __init__(
        self,
        schema_svc: SchemaIndexService,
        prompt_builder: PromptBuilder | None = None,
        clarification_svc: ClarificationService | None = None,
    ):
        self._schema_svc = schema_svc
        self._prompt = prompt_builder or PromptBuilder()
        self._clarify = clarification_svc or ClarificationService()
        self._client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )
        self._model = settings.LLM_LIGHT_MODEL

    async def classify(
        self, question: str, user_ctx: UserContext
    ) -> IntentResult:
        """Classify a user question. Raises ClassificationError only if all layers fail."""
        module_index = self._schema_svc.get_module_index_text()
        system_prompt = self._prompt.build(module_index, user_ctx)

        # Layer 1: json_schema strict mode
        result = await self._call_with_schema(system_prompt, question)
        if result:
            return result

        # Layer 2: json_object mode
        result = await self._call_with_json_object(system_prompt, question)
        if result:
            return result

        # Layer 3: raise for controller to trigger clarification
        raise ClassificationError("Intent classification failed at all LLM layers")

    async def _call_with_schema(
        self, system_prompt: str, question: str
    ) -> IntentResult | None:
        try:
            resp = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "intent_result",
                            "strict": True,
                            "schema": INTENT_JSON_SCHEMA,
                        },
                    },
                    temperature=0.1,
                    max_tokens=500,
                ),
                timeout=5.0,
            )
            raw = resp.choices[0].message.content
            return IntentResult.model_validate_json(raw)
        except (ValidationError, asyncio.TimeoutError, Exception) as e:
            logger.warning("json_schema mode failed: %s", e)
            return None

    async def _call_with_json_object(
        self, system_prompt: str, question: str
    ) -> IntentResult | None:
        try:
            resp = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.15,
                    max_tokens=500,
                ),
                timeout=8.0,
            )
            raw = resp.choices[0].message.content
            return IntentResult.model_validate_json(raw)
        except (ValidationError, asyncio.TimeoutError, Exception) as e:
            logger.warning("json_object fallback failed: %s", e)
            return None

    def get_clarification_options(
        self, question: str, user_ctx: UserContext
    ) -> list:
        """Generate clarification options after classification failure."""
        return self._clarify.generate_options(question, user_ctx)

    def save_unmatched(self, question: str, user_ctx: UserContext) -> None:
        """Save unmatched question for future analysis."""
        self._clarify.save_unmatched(question, user_ctx)
