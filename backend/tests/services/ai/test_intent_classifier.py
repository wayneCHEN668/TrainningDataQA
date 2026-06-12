"""Unit tests for intent classification (no live LLM required)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.schemas.intent import IntentResult, SlotValues, ClarificationOption
from app.schemas.auth import UserContext
from app.services.ai.intent_definitions import (
    INTENT_DEFINITIONS,
    get_intent_list_for_prompt,
    get_intent_enum_values,
)
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.clarification import ClarificationService
from app.services.ai.intent_classifier import (
    IntentClassifier,
    ClassificationError,
    INTENT_JSON_SCHEMA,
)


# --- Test fixtures ---

@pytest.fixture
def user_ctx():
    return UserContext(
        user_id="u1",
        user_code="admin001",
        user_name="Test Admin",
        role_level=1,
        dept_code="D001",
    )


# --- Pydantic model tests (5 tests) ---

class TestIntentResult:
    def test_valid_full_json(self):
        data = {
            "intent": "EXAM_PASS_RATE_QUERY",
            "confidence": 0.95,
            "complexity": "simple",
            "slots": {"time_range": {"type": "this_month"}, "scope_type": "all"},
            "need_clarification": False,
            "clarification_question": None,
        }
        result = IntentResult.model_validate(data)
        assert result.intent == "EXAM_PASS_RATE_QUERY"
        assert result.confidence == 0.95

    def test_intent_field_is_required(self):
        """Only 'intent' has no default; all other fields have defaults."""
        # Validate that just providing intent works
        result = IntentResult(intent="EXAM_PASS_RATE_QUERY")
        assert result.intent == "EXAM_PASS_RATE_QUERY"
        assert result.confidence == 0.0  # default
        assert result.complexity == "simple"  # default
        assert result.need_clarification is False  # default
        assert isinstance(result.slots, SlotValues)

    def test_default_slot_values(self):
        slot = SlotValues()
        assert slot.scope_type == "all"
        assert slot.top_n == 10
        assert slot.granularity == "week"

    def test_json_schema_has_intent_enum(self):
        props = INTENT_JSON_SCHEMA["properties"]
        assert "enum" in props["intent"]
        assert len(props["intent"]["enum"]) == 22

    def test_slot_values_custom(self):
        slot = SlotValues(
            time_range={"type": "custom", "start": "2026-01-01", "end": "2026-06-01"},
            scope_type="dept",
            scope_name="海淀支行",
            top_n=20,
        )
        assert slot.scope_name == "海淀支行"
        assert slot.top_n == 20


# --- Intent definitions tests (4 tests) ---

class TestIntentDefinitions:
    def test_22_intents(self):
        assert len(INTENT_DEFINITIONS) == 22

    def test_no_duplicate_intents(self):
        codes = [d["intent"] for d in INTENT_DEFINITIONS]
        assert len(codes) == len(set(codes))

    def test_all_have_required_fields(self):
        for d in INTENT_DEFINITIONS:
            assert "intent" in d
            assert "label" in d
            assert "complexity" in d
            assert d["complexity"] in ("simple", "moderate", "complex")

    def test_enum_values_match_definitions(self):
        enum_values = get_intent_enum_values()
        codes = [d["intent"] for d in INTENT_DEFINITIONS]
        assert set(enum_values) == set(codes)


# --- Prompt builder tests (1 test) ---

class TestPromptBuilder:
    def test_build_includes_user_context(self, user_ctx):
        builder = PromptBuilder()
        prompt = builder.build("## Modules\n- M5: exams", user_ctx)
        assert "Test Admin" in prompt
        assert "M5: exams" in prompt
        assert "EXAM_PASS_RATE_QUERY" in prompt


# --- Clarification service tests (4 tests) ---

class TestClarificationService:
    def test_generates_3_options(self, user_ctx):
        svc = ClarificationService()
        options = svc.generate_options("考试通过率怎么样", user_ctx)
        assert len(options) == 3
        assert all(isinstance(o, ClarificationOption) for o in options)
        assert options[0].index == 1
        assert options[2].index == 3

    def test_keyword_match_exam(self, user_ctx):
        svc = ClarificationService()
        options = svc.generate_options("最近考试通过率如何", user_ctx)
        intents = [o.intent for o in options]
        assert "EXAM_PASS_RATE_QUERY" in intents

    def test_falls_back_to_default_on_no_match(self, user_ctx):
        svc = ClarificationService()
        options = svc.generate_options("随便问一句", user_ctx)
        assert len(options) == 3

    def test_scope_replaced_in_text(self, user_ctx):
        svc = ClarificationService()
        options = svc.generate_options("完成率怎么样", user_ctx)
        # dept_code is D001, should appear in generated text
        assert any("D001" in o.text for o in options)


# --- IntentClassifier with mocked LLM (3 tests) ---

class TestIntentClassifier:
    @pytest.fixture
    def mock_schema_svc(self):
        svc = MagicMock()
        svc.get_module_index_text.return_value = "## Modules\n- M5: exams"
        return svc

    @pytest.mark.asyncio
    async def test_classify_success_schema_mode(self, mock_schema_svc, user_ctx):
        classifier = IntentClassifier(schema_svc=mock_schema_svc)
        mock_result = IntentResult(
            intent="EXAM_PASS_RATE_QUERY",
            confidence=0.95,
            complexity="simple",
            slots=SlotValues(time_range={"type": "this_month"}, scope_type="all"),
            need_clarification=False,
        )
        with patch.object(classifier, "_call_with_schema", AsyncMock(return_value=mock_result)):
            result = await classifier.classify("测试问题", user_ctx)
            assert result.intent == "EXAM_PASS_RATE_QUERY"

    @pytest.mark.asyncio
    async def test_falls_back_to_json_object(self, mock_schema_svc, user_ctx):
        classifier = IntentClassifier(schema_svc=mock_schema_svc)
        mock_result = IntentResult(
            intent="COMPLETION_RATE_QUERY",
            confidence=0.85,
            complexity="simple",
            slots=SlotValues(time_range={"type": "this_month"}, scope_type="all"),
            need_clarification=False,
        )
        with patch.object(classifier, "_call_with_schema", AsyncMock(return_value=None)):
            with patch.object(classifier, "_call_with_json_object", AsyncMock(return_value=mock_result)):
                result = await classifier.classify("测试", user_ctx)
                assert result.intent == "COMPLETION_RATE_QUERY"

    @pytest.mark.asyncio
    async def test_raises_classification_error_on_double_failure(self, mock_schema_svc, user_ctx):
        classifier = IntentClassifier(schema_svc=mock_schema_svc)
        with patch.object(classifier, "_call_with_schema", AsyncMock(return_value=None)):
            with patch.object(classifier, "_call_with_json_object", AsyncMock(return_value=None)):
                with pytest.raises(ClassificationError):
                    await classifier.classify("测试", user_ctx)
