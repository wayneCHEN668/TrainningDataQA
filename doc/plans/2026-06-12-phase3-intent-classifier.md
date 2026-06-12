# Phase 3 意图识别层 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 IntentClassifier 意图识别引擎——LLM Call #1，将自然语言问题转化为结构化意图+槽位。双层调用（json_schema 主路径 + json_object 降级），失败后关键词追问降级。

**Architecture:** SchemaIndexService 提供模块索引上下文 → IntentClassifier 拼接 System Prompt → 调用轻量 LLM → Pydantic 解析结构化输出 → 失败则 ClarificationService 生成 3 个追问选项。

**Tech Stack:** Python 3.12, openai SDK (httpx), Pydantic v2, SchemaIndexService (已有)

---

### Task 1: LLM 配置 + 依赖

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add LLM config fields to backend/app/core/config.py**

Add these fields to the Settings class (before `model_config`):

```python
# LLM 通用配置
LLM_BASE_URL: str = "http://localhost:8000/v1"
LLM_API_KEY: str = "not-needed"

# 意图识别用轻量模型（Phase 3）
LLM_LIGHT_MODEL: str = "qwen2.5-7b-instruct"

# ReAct 推理用重量模型（Phase 5 预留）
LLM_HEAVY_MODEL: str = "qwen2.5-72b-instruct"
```

Remove the old single `LLM_BASE_URL` and `LLM_MODEL` fields (they were placeholders from Task 2).

- [ ] **Step 2: Update backend/.env.example**

Replace old LLM lines with:
```
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=not-needed
LLM_LIGHT_MODEL=qwen2.5-7b-instruct
LLM_HEAVY_MODEL=qwen2.5-72b-instruct
```

- [ ] **Step 3: Add openai SDK to pyproject.toml dependencies**

Add `"openai>=1.0.0",` to `[project] dependencies`.

- [ ] **Step 4: Install deps and verify**

```bash
cd backend && pip install -e ".[dev]"
python -c "from app.core.config import settings; print(settings.LLM_LIGHT_MODEL)"
```
Expected: prints `qwen2.5-7b-instruct`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/.env.example backend/pyproject.toml
git commit -m "feat: add LLM config fields (light/heavy model, api key)"
```

---

### Task 2: Pydantic 数据模型

**Files:**
- Create: `backend/app/schemas/intent.py`

- [ ] **Step 1: Write backend/app/schemas/intent.py**

```python
"""Intent classification data models."""
from pydantic import BaseModel, Field


class SlotValues(BaseModel):
    """Query slots extracted from user question."""
    time_range: dict = Field(
        default_factory=lambda: {"type": "this_month"},
        description="Time range: {type: today/this_week/this_month/last_month/custom, start: YYYY-MM-DD, end: YYYY-MM-DD}"
    )
    scope_type: str = Field(
        default="all",
        description="Scope: all/org/dept/class/individual"
    )
    scope_name: str | None = Field(default=None)
    course_name: str | None = Field(default=None)
    exam_name: str | None = Field(default=None)
    metric: str | None = Field(default=None)
    compare_with_previous: bool = Field(default=False)
    top_n: int = Field(default=10, ge=1, le=100)
    granularity: str = Field(default="week", description="day/week/month")


class IntentResult(BaseModel):
    """Full intent classification result."""
    intent: str = Field(description="One of 22 intent codes")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    complexity: str = Field(default="simple", description="simple/moderate/complex")
    slots: SlotValues = Field(default_factory=SlotValues)
    need_clarification: bool = Field(default=False)
    clarification_question: str | None = Field(default=None)


class ClarificationOption(BaseModel):
    """Rephrased question option for user selection."""
    index: int = Field(ge=1, le=3)
    text: str
    intent: str
```

- [ ] **Step 2: Verify import and JSON schema generation**

```bash
cd backend && python -c "
from app.schemas.intent import IntentResult, SlotValues
schema = IntentResult.model_json_schema()
assert 'intent' in schema['properties']
assert 'confidence' in schema['properties']
print('IntentResult schema generated OK')
print('Properties:', list(schema['properties'].keys()))
"
```
Expected: prints properties list with intent, confidence, complexity, slots, need_clarification, clarification_question.

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/intent.py
git commit -m "feat: add intent classification Pydantic models (IntentResult, SlotValues, ClarificationOption)"
```

---

### Task 3: 22 意图定义 + System Prompt 构建

**Files:**
- Create: `backend/app/services/ai/intent_definitions.py`
- Create: `backend/app/services/ai/prompt_builder.py`

- [ ] **Step 1: Write backend/app/services/ai/intent_definitions.py**

```python
"""22 intent definitions for the intent classifier."""

INTENT_DEFINITIONS = [
    {"intent": "COMPLETION_RATE_QUERY",    "label": "完成率查询",    "complexity": "simple",   "keywords": "完成率/完成情况/没完成"},
    {"intent": "INCOMPLETE_LEARNER_QUERY", "label": "未完成学员查询", "complexity": "simple",   "keywords": "谁没学完/未提交/逾期"},
    {"intent": "LEARNING_PROGRESS_QUERY",  "label": "学习进度查询",  "complexity": "simple",   "keywords": "进度/学到哪/完成了几个"},
    {"intent": "LEARNING_DURATION_QUERY",  "label": "学习时长查询",  "complexity": "simple",   "keywords": "学了多久/时长/花多少时间"},
    {"intent": "EXAM_SCORE_QUERY",         "label": "考试成绩查询",  "complexity": "simple",   "keywords": "成绩/分数/平均分/得了多少"},
    {"intent": "EXAM_PASS_RATE_QUERY",     "label": "考试通过率查询", "complexity": "simple",   "keywords": "通过率/及格率/过了多少人"},
    {"intent": "SKILL_ERROR_QUERY",        "label": "技能点错误分析", "complexity": "moderate", "keywords": "操作错误/哪步出错/错误率"},
    {"intent": "COMPREHENSIVE_GRADE_QUERY","label": "综合成绩查询",  "complexity": "simple",   "keywords": "综合成绩/总分/结业"},
    {"intent": "PERFORMANCE_RANKING_QUERY","label": "成绩排名",      "complexity": "simple",   "keywords": "排名/前几名/最好最差/倒数"},
    {"intent": "LEARNING_TREND_QUERY",     "label": "学习趋势分析",  "complexity": "moderate", "keywords": "趋势/变化/走势/这几个月"},
    {"intent": "ORG_OVERVIEW_QUERY",       "label": "机构概览",      "complexity": "moderate", "keywords": "整体情况/概览/汇总/总结"},
    {"intent": "ORG_COMPARISON_QUERY",     "label": "机构对比",      "complexity": "moderate", "keywords": "对比/哪个最好/差距/比较"},
    {"intent": "AT_RISK_LEARNER_QUERY",    "label": "风险学员识别",  "complexity": "moderate", "keywords": "风险/需要关注/有问题的"},
    {"intent": "COMPLIANCE_RISK_QUERY",    "label": "合规风险查询",  "complexity": "moderate", "keywords": "合规/监管/达标/未达标"},
    {"intent": "INDIVIDUAL_PROFILE_QUERY", "label": "个人学习画像",  "complexity": "moderate", "keywords": "某个人的情况/某某怎么样"},
    {"intent": "ROOT_CAUSE_ANALYSIS",      "label": "根因分析",      "complexity": "complex",  "keywords": "为什么/原因/怎么解释"},
    {"intent": "ANOMALY_INVESTIGATION",    "label": "异常调查",      "complexity": "complex",  "keywords": "异常/突然/为什么这时候"},
    {"intent": "COMPARATIVE_DIAGNOSIS",    "label": "对比诊断",      "complexity": "complex",  "keywords": "差距从哪来/为什么A比B好"},
    {"intent": "COMPLETION_PREDICTION",    "label": "完成情况预测",  "complexity": "moderate", "keywords": "预测/按现在进度/能完成吗"},
    {"intent": "RISK_PREDICTION",          "label": "风险预测",      "complexity": "moderate", "keywords": "可能不及格/有没有风险"},
    {"intent": "IMPROVEMENT_SUGGESTION",   "label": "改进建议",      "complexity": "complex",  "keywords": "建议/怎么提升/如何改善"},
    {"intent": "TRAINING_PLANNING",        "label": "培训规划",      "complexity": "complex",  "keywords": "规划/下一步/重点培训什么"},
]


def get_intent_list_for_prompt() -> str:
    """Format 22 intents as a prompt-friendly table."""
    lines = ["## Supported Intents (22 total)"]
    for d in INTENT_DEFINITIONS:
        lines.append(
            f"- {d['intent']} | {d['label']} | complexity={d['complexity']} | triggers: {d['keywords']}"
        )
    return "\n".join(lines)


def get_intent_enum_values() -> list[str]:
    """Return all 22 intent codes for JSON schema enum constraint."""
    return [d["intent"] for d in INTENT_DEFINITIONS]
```

- [ ] **Step 2: Write backend/app/services/ai/prompt_builder.py**

```python
"""Build the system prompt for intent classification."""
from datetime import datetime
from app.schemas.auth import UserContext
from app.services.ai.intent_definitions import get_intent_list_for_prompt

ROLE_DECLARATION = """You are the intent classification engine for the SkillCloudHS training data analysis system.
Your ONLY job is to classify user questions and extract query parameters.
Do NOT try to answer the question. Only output structured JSON."""

SLOT_EXTRACTION_RULES = """## Slot Extraction Rules

time_range: today -> today | this week -> this_week | this month -> this_month | last month -> last_month
             this quarter -> this_quarter | this year -> this_year
             last N days/weeks/months -> custom (calculate start/end based on current date)

scope_type: not specified -> all | mentions specific org/branch -> org
            mentions class -> class | mentions a person's name -> individual

IMPORTANT: If the question contains "why" or "reason" words, force complexity=complex.
IMPORTANT: If the question is vague (e.g., "how is everything going"), set need_clarification=true."""

OUTPUT_INSTRUCTION = "Output ONLY valid JSON. No markdown, no extra text."


class PromptBuilder:
    """Builds the full system prompt for the intent classification LLM call."""

    def __init__(self):
        self._intent_table = get_intent_list_for_prompt()

    def build(
        self,
        module_index_text: str,
        user_ctx: UserContext,
    ) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        dynamic = f"""## Current Context
User: {user_ctx.user_name}
Role: level={user_ctx.role_level}, dept={user_ctx.dept_code}
Time: {now}

{module_index_text}"""

        return "\n\n".join([
            ROLE_DECLARATION,
            dynamic,
            self._intent_table,
            SLOT_EXTRACTION_RULES,
            OUTPUT_INSTRUCTION,
        ])
```

- [ ] **Step 3: Verify imports**

```bash
cd backend && python -c "
from app.services.ai.intent_definitions import INTENT_DEFINITIONS, get_intent_list_for_prompt, get_intent_enum_values
from app.services.ai.prompt_builder import PromptBuilder
assert len(INTENT_DEFINITIONS) == 22
assert len(get_intent_enum_values()) == 22
print('22 intents verified')
print(get_intent_list_for_prompt()[:200])
"
```
Expected: prints `22 intents verified` and first 200 chars of intent table.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ai/intent_definitions.py backend/app/services/ai/prompt_builder.py
git commit -m "feat: add 22 intent definitions and prompt builder"
```

---

### Task 4: ClarificationService（追问降级）

**Files:**
- Create: `backend/app/services/ai/clarification.py`

- [ ] **Step 1: Write backend/app/services/ai/clarification.py**

```python
"""Clarification service: generates rephrased question options when LLM intent classification fails."""
import re
from datetime import datetime
from pathlib import Path
from app.schemas.auth import UserContext
from app.schemas.intent import ClarificationOption

FALLBACK_TEMPLATES = [
    {
        "keywords": ["完成", "学完", "进度", "没做"],
        "rephrases": [
            ("查询{scope}各院系的课件完成率", "COMPLETION_RATE_QUERY"),
            ("查询{scope}未完成学习的学员名单", "INCOMPLETE_LEARNER_QUERY"),
            ("查询{scope}学习进度的整体概况", "LEARNING_PROGRESS_QUERY"),
        ],
    },
    {
        "keywords": ["考试", "成绩", "分数", "通过", "及格"],
        "rephrases": [
            ("查询{scope}各院系的考试通过率", "EXAM_PASS_RATE_QUERY"),
            ("查询{scope}考试成绩排名情况", "PERFORMANCE_RANKING_QUERY"),
            ("查询{scope}考试中错误率最高的题目", "SKILL_ERROR_QUERY"),
        ],
    },
    {
        "keywords": ["学.*多久", "时长", "时间", "花.*小时"],
        "rephrases": [
            ("查询{scope}的学习时长统计", "LEARNING_DURATION_QUERY"),
            ("查询{scope}学习时长的月度趋势", "LEARNING_TREND_QUERY"),
            ("查询{scope}学习时长最少的学员", "AT_RISK_LEARNER_QUERY"),
        ],
    },
    {
        "keywords": ["综合", "总分", "结业", "加权"],
        "rephrases": [
            ("查询{scope}学员综合成绩概况", "COMPREHENSIVE_GRADE_QUERY"),
            ("查询{scope}各院系综合成绩对比", "ORG_COMPARISON_QUERY"),
            ("查询{scope}未达到结业标准的学员", "COMPLIANCE_RISK_QUERY"),
        ],
    },
    {
        "keywords": ["为什么", "原因", "怎么解释", "解释"],
        "rephrases": [
            ("分析{scope}学习数据变化的根因", "ROOT_CAUSE_ANALYSIS"),
            ("调查{scope}数据异常的原因", "ANOMALY_INVESTIGATION"),
            ("对比分析{scope}与平均水平的差距原因", "COMPARATIVE_DIAGNOSIS"),
        ],
    },
    {
        "keywords": ["建议", "提升", "改善", "改进"],
        "rephrases": [
            ("基于{scope}的学习数据生成改进建议", "IMPROVEMENT_SUGGESTION"),
            ("为{scope}规划下一步培训重点", "TRAINING_PLANNING"),
            ("预测{scope}按当前进度能否完成培训", "COMPLETION_PREDICTION"),
        ],
    },
]

# Default template when no keywords match
_DEFAULT_TEMPLATE = FALLBACK_TEMPLATES[0]

UNMATCHED_QUERIES_PATH = Path("../doc/unmatched_queries.md")


class ClarificationService:
    """Generate rephrased question options for user clarification."""

    def generate_options(
        self, question: str, user_ctx: UserContext
    ) -> list[ClarificationOption]:
        scope = user_ctx.dept_code or "全部"
        matched = self._match_keywords(question)
        if not matched:
            matched = _DEFAULT_TEMPLATE
        return [
            ClarificationOption(
                index=i + 1,
                text=text.format(scope=scope),
                intent=intent,
            )
            for i, (text, intent) in enumerate(matched["rephrases"])
        ]

    def _match_keywords(self, question: str) -> dict | None:
        for template in FALLBACK_TEMPLATES:
            for kw in template["keywords"]:
                if re.search(kw, question):
                    return template
        return None

    def save_unmatched(
        self, question: str, user_ctx: UserContext
    ) -> None:
        """Append unmatched question to doc/unmatched_queries.md."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        role_map = {0: "superadmin", 1: "admin", 2: "teacher", 3: "student"}
        role = role_map.get(user_ctx.role_level, "unknown")

        line = f"| {now} | {user_ctx.user_name} | {role} | {question} |\n"

        path = UNMATCHED_QUERIES_PATH
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Unmatched User Questions\n\n"
                "| Time | User | Role | Question |\n"
                "|------|------|------|----------|\n"
            )

        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "
from app.services.ai.clarification import ClarificationService
svc = ClarificationService()
print('ClarificationService import OK')
"
```
Expected: `ClarificationService import OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ai/clarification.py
git commit -m "feat: add ClarificationService with keyword-based fallback and unmatched query logging"
```

---

### Task 5: IntentClassifier 核心实现

**Files:**
- Create: `backend/app/services/ai/intent_classifier.py`

- [ ] **Step 1: Write backend/app/services/ai/intent_classifier.py**

```python
"""Intent classifier: LLM Call #1 with dual-layer fallback."""
import asyncio
import json
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
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "
from app.services.ai.intent_classifier import IntentClassifier, ClassificationError
print('IntentClassifier import OK')
print('JSON schema has', len(INTENT_JSON_SCHEMA['properties']), 'properties')
"
```
Expected: prints import OK and 5 properties (intent, confidence, complexity, slots, need_clarification).

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ai/intent_classifier.py
git commit -m "feat: implement IntentClassifier with dual-layer LLM fallback strategy"
```

---

### Task 6: 单元测试

**Files:**
- Create: `backend/tests/services/ai/test_intent_classifier.py`

- [ ] **Step 1: Write the tests**

```python
"""Unit tests for intent classification (no live LLM required)."""
import json
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


# --- Pydantic model tests ---

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

    def test_missing_required_field_fails(self):
        data = {"intent": "EXAM_PASS_RATE_QUERY"}
        with pytest.raises(Exception):
            IntentResult.model_validate(data)

    def test_invalid_intent_fails(self):
        data = {
            "intent": "NOT_A_REAL_INTENT",
            "confidence": 0.5,
            "complexity": "simple",
            "slots": {"time_range": {"type": "today"}, "scope_type": "all"},
            "need_clarification": False,
            "clarification_question": None,
        }
        with pytest.raises(Exception):
            IntentResult.model_validate(data)

    def test_default_slot_values(self):
        slot = SlotValues()
        assert slot.scope_type == "all"
        assert slot.top_n == 10
        assert slot.granularity == "week"

    def test_json_schema_has_intent_enum(self):
        props = INTENT_JSON_SCHEMA["properties"]
        assert "enum" in props["intent"]
        assert len(props["intent"]["enum"]) == 22


# --- Intent definitions tests ---

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


# --- Prompt builder tests ---

class TestPromptBuilder:
    def test_build_includes_user_context(self, user_ctx):
        builder = PromptBuilder()
        prompt = builder.build("## Modules\n- M5: exams", user_ctx)
        assert "Test Admin" in prompt
        assert "M5: exams" in prompt
        assert "EXAM_PASS_RATE_QUERY" in prompt


# --- Clarification service tests ---

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
        assert "EXAM_PASS_RATE_QUERY" in [o.intent for o in options]

    def test_falls_back_to_default_on_no_match(self, user_ctx):
        svc = ClarificationService()
        options = svc.generate_options("随便问一句", user_ctx)
        assert len(options) == 3


# --- IntentClassifier with mocked LLM ---

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
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/services/ai/test_intent_classifier.py -v
```
Expected: all tests pass (14+ tests).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/services/ai/test_intent_classifier.py
git commit -m "test: add IntentClassifier unit tests (14 tests, no LLM required)"
```

---

### Task 7: Cleanup + Verification

- [ ] **Step 1: Run all existing tests to ensure no regressions**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all tests pass (10 schema_index + 14 intent_classifier = 24 tests).

- [ ] **Step 2: Verify all new imports**

```bash
cd backend && python -c "
from app.schemas.intent import IntentResult, SlotValues, ClarificationOption
from app.services.ai.intent_definitions import INTENT_DEFINITIONS, get_intent_enum_values
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.clarification import ClarificationService
from app.services.ai.intent_classifier import IntentClassifier, ClassificationError
print('All Phase 3 imports OK')
"
```
Expected: `All Phase 3 imports OK`.

- [ ] **Step 3: Verify config fields**

```bash
cd backend && python -c "
from app.core.config import settings
print('LLM_BASE_URL:', settings.LLM_BASE_URL)
print('LLM_LIGHT_MODEL:', settings.LLM_LIGHT_MODEL)
print('LLM_HEAVY_MODEL:', settings.LLM_HEAVY_MODEL)
"
```
Expected: prints all three config values.

- [ ] **Step 4: Remove generator script and commit**

```bash
rm doc/plans/gen_phase3_plan.py
git add -A
git commit -m "chore: Phase 3 integration verification passed"
```

---

## Task Dependencies

```
Task 1 (LLM config + deps)
  └─> Task 2 (Pydantic models)
       └─> Task 3 (22 intents + prompt builder)
            ├─> Task 5 (IntentClassifier core)
            │    └─> Task 6 (unit tests)
            │         └─> Task 7 (verification)
            └─> Task 4 (ClarificationService)
                 └─> (independent of Task 5, can be parallel)
```

## Time Estimate

| Task | Time | Risk |
|------|------|------|
| 1: LLM config + deps | 10 min | None |
| 2: Pydantic models | 10 min | None |
| 3: 22 intents + prompt builder | 15 min | None |
| 4: ClarificationService | 15 min | None |
| 5: IntentClassifier core | 20 min | Async OpenAI client setup |
| 6: Unit tests (14 tests) | 20 min | Mock setup |
| 7: Verification | 10 min | None |
| **Total** | **~1.75 hours** | |
