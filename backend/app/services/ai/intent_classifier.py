"""Intent classifier: LLM Call #1 with dual-layer fallback."""
import asyncio
import json
import logging
import time
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


def _repair_truncated_json(raw: str) -> str:
    """Attempt to repair truncated JSON by closing open brackets/braces.

    When max_tokens is too small, the LLM output gets cut off mid-object,
    e.g. '{"intent": "X", "slots": {"scope_ty'

    Strategy:
    1. Track bracket depth and string state
    2. Find the last complete key-value pair (at a comma)
    3. Close any open objects/arrays
    """
    if not raw or not raw.strip():
        return raw

    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escape = False

    for ch in raw:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth_brace += 1
            elif ch == "}":
                depth_brace -= 1
            elif ch == "[":
                depth_bracket += 1
            elif ch == "]":
                depth_bracket -= 1

    if depth_brace == 0 and depth_bracket == 0:
        return raw

    # Find last comma at correct depth for clean truncation
    last_valid_pos = len(raw)
    t_brace = 0
    t_bracket = 0
    t_in_string = False
    t_escape = False

    for i, ch in enumerate(raw):
        if t_in_string:
            if t_escape:
                t_escape = False
            elif ch == "\\":
                t_escape = True
            elif ch == '"':
                t_in_string = False
        else:
            if ch == '"':
                t_in_string = True
            elif ch == "{":
                t_brace += 1
            elif ch == "}":
                t_brace -= 1
            elif ch == "[":
                t_bracket += 1
            elif ch == "]":
                t_bracket -= 1
            elif ch == ",":
                last_valid_pos = i

    repaired = raw[:last_valid_pos].rstrip().rstrip(",")
    repaired += "]" * max(t_bracket, 0)
    repaired += "}" * max(t_brace, 0)
    return repaired


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
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["today", "this_week", "this_month", "last_month", "this_quarter", "this_year", "custom"]},
                            "start": {"type": ["string", "null"]},
                            "end": {"type": ["string", "null"]},
                        },
                        "required": ["type"],
                    },
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

        print(f"[IntentClassifier] LLM Base URL: {settings.LLM_BASE_URL}", flush=True)
        print(f"[IntentClassifier] LLM Model: {self._model}", flush=True)

        # Layer 1 (json_schema strict mode) removed — not supported by DeepSeek/大多数模型
        # 直接走 Layer 2: json_object mode (with retry for transient failures)
        print("[IntentClassifier] json_object mode...", flush=True)
        t2 = time.monotonic()
        result = await self._call_with_json_object_retry(system_prompt, question)
        if result:
            print(f"[IntentClassifier] 成功, 耗时: {(time.monotonic()-t2)*1000:.0f}ms", flush=True)
            # 检测报表关键词，设置 output_mode
            report_keywords = ["报表", "导出", "生成Excel", "生成excel", "下载", "导出数据", "生成报告"]
            if any(kw in question for kw in report_keywords):
                result.output_mode = "report"
            return result
        print("[IntentClassifier] 失败", flush=True)

        # Fallback: raise for controller to trigger clarification
        print("[IntentClassifier] 所有层均失败, 抛出 ClassificationError", flush=True)
        raise ClassificationError("Intent classification failed at all LLM layers")

    async def _call_with_json_object_retry(
        self, system_prompt: str, question: str, max_retries: int = 1
    ) -> IntentResult | None:
        """Wrap _call_with_json_object with retry on transient failures.

        Retries once on timeout or retryable exceptions to reduce
        classification instability caused by network jitter.
        """
        last_result = None
        for attempt in range(max_retries + 1):
            last_result = await self._call_with_json_object(system_prompt, question)
            if last_result is not None:
                return last_result
            if attempt < max_retries:
                print(f"[IntentClassifier] 重试 {attempt + 1}/{max_retries}...", flush=True)
                await asyncio.sleep(2 ** attempt)
        return last_result

    async def _call_with_json_object(
        self, system_prompt: str, question: str
    ) -> IntentResult | None:
        try:
            print("[IntentClassifier] Layer 2: 发送 LLM 请求...", flush=True)
            t0 = time.monotonic()
            resp = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0,  # P0 fix: deterministic output for stability
                    max_tokens=2000,  # P0 fix: 500 was too small, caused truncation
                ),
                timeout=30.0,
            )
            elapsed = (time.monotonic() - t0) * 1000
            print(f"[IntentClassifier] Layer 2: LLM 响应到达, 耗时: {elapsed:.0f}ms", flush=True)
            raw = resp.choices[0].message.content
            print(f"[IntentClassifier] Layer 2: 原始响应 ({len(raw)} chars): {raw[:200]}", flush=True)

            # Check finish_reason — if truncated, attempt JSON repair
            finish_reason = resp.choices[0].finish_reason
            if finish_reason == "length":
                print(f"[IntentClassifier] Layer 2: 响应被截断 (finish_reason=length), 尝试修复...", flush=True)
                repaired = _repair_truncated_json(raw)
                if repaired != raw:
                    print(f"[IntentClassifier] Layer 2: JSON 修复后 ({len(repaired)} chars): {repaired[:200]}", flush=True)
                    raw = repaired

            return IntentResult.model_validate_json(raw)
        except asyncio.TimeoutError:
            print("[IntentClassifier] Layer 2: 超时 (30s)", flush=True)
            logger.warning("json_object fallback timed out")
            return None
        except ValidationError as e:
            print(f"[IntentClassifier] Layer 2: Pydantic 校验失败: {e}", flush=True)
            logger.warning("json_object fallback failed: %s", e)
            return None
        except Exception as e:
            print(f"[IntentClassifier] Layer 2: 异常 {type(e).__name__}: {e}", flush=True)
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