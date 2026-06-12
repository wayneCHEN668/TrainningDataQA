# Phase 3 — 意图识别层 设计文档

**项目**: SkillCloudHS AI 数据问答系统
**日期**: 2026-06-12
**状态**: 已确认（待用户评审）

---

## 1. 概述

Phase 3 实现意图识别引擎（IntentClassifier），作为 AI 问答流程的 LLM 调用 #1。将用户的自然语言问题转化为结构化的意图（22 种之一）+ 槽位参数，供后续 ReAct 推理引擎使用。

### 1.1 核心指标

| 指标 | 要求 |
|------|------|
| 意图分类准确率 | >= 92%（22 意图测试集） |
| 主路径响应时间 | < 1.0s（轻量模型，7B 级别） |
| 降级路径响应时间 | < 3.0s |
| 模块索引注入 token | ~400 tokens（不超 600） |

---

## 2. 核心组件与数据流

```
用户问题 "上季度 A 支行考试通过率为什么降了？"
  |
  v
POST /api/v1/ai-query  (Phase 5 SSE 端点)
  |
  v
IntentClassifier.classify(question, user_context)
  |
  +-- 1. 从 SchemaIndexService 获取 module_index_text (~400 tokens)
  |
  +-- 2. 构建 system prompt (用户上下文 + 当前时间 + 模块索引 + 22意图定义 + 槽位规则)
  |
  +-- 3. LLM Call #1 -- 主路径: json_schema strict mode
  |     +-- 成功 -> Pydantic IntentResult.model_validate_json()
  |     +-- 失败 -> 降级: json_object mode
  |           +-- 成功 -> Pydantic IntentResult.model_validate_json()
  |           +-- 失败 -> 追问式降级 (ClarificationService)
  |
  +-- 4. 返回 IntentResult(intent, confidence, complexity, slots)
```

### 2.1 产出文件

```
backend/app/services/ai/
  schema_index.py            # 已存在 (Phase 1)
  intent_classifier.py       # 新建 -- IntentClassifier
  clarification.py           # 新建 -- ClarificationService

backend/app/schemas/
  intent.py                  # 新建 -- IntentResult, SlotValues, ClarificationOption
```

---

## 3. Pydantic 数据模型

### 3.1 SlotValues

```python
class SlotValues(BaseModel):
    time_range: dict = Field(
        default_factory=lambda: {"type": "this_month"}
    )
    scope_type: str = Field(default="all")
    scope_name: str | None = None
    course_name: str | None = None
    exam_name: str | None = None
    metric: str | None = None
    compare_with_previous: bool = False
    top_n: int = Field(default=10, ge=1, le=100)
    granularity: str = Field(default="week")
```

### 3.2 IntentResult

```python
class IntentResult(BaseModel):
    intent: str          # 22个意图之一
    confidence: float    # [0, 1]
    complexity: str      # simple/moderate/complex
    slots: SlotValues
    need_clarification: bool = False
    clarification_question: str | None = None
```

### 3.3 ClarificationOption

```python
class ClarificationOption(BaseModel):
    index: int           # 1/2/3
    text: str            # 转述后的自然语言问题
    intent: str          # 对应的意图码
```

---

## 4. System Prompt 设计

### 4.1 模板结构

System Prompt 由四部分拼接:

1. **角色声明** -- "你是 SkillCloudHS 培训数据分析系统的意图识别引擎。只做分类和参数提取，不尝试回答问题。"
2. **运行时动态上下文** -- 用户名 + 角色 + 权限范围 + 当前时间 + 模块索引（来自 SchemaIndexService，~400 tokens）
3. **22 意图定义表** -- 意图码 | 中文名称 | 复杂度 | 触发关键词（静态，写死在代码中）
4. **槽位提取规则** -- time_range 推断、scope_type 推断、"为什么/原因" -> complexity=complex
5. **输出指令** -- "只返回 JSON，不带 markdown 或其他文字"

### 4.2 22 Intent Definitions

```python
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
```

---

## 5. 双层调用 + 容错

### 5.1 主路径: json_schema strict mode

```python
async def _call_with_schema(self, system_prompt: str, question: str) -> IntentResult | None:
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
    except (ValidationError, asyncio.TimeoutError, Exception):
        return None
```

### 5.2 降级: json_object mode

```python
async def _call_with_json_object(self, system_prompt: str, question: str) -> IntentResult | None:
    try:
        resp = await asyncio.wait_for(
            self._client.chat.completions.create(
                model=self._model,
                messages=[...],
                response_format={"type": "json_object"},
                temperature=0.15,
                max_tokens=500,
            ),
            timeout=8.0,
        )
        return IntentResult.model_validate_json(resp.choices[0].message.content)
    except (ValidationError, asyncio.TimeoutError, Exception):
        return None
```

### 5.3 追问式降级（替代硬失败）

双层 LLM 调用都失败后，不返回 503。改用关键词匹配生成 3 个转述选项：

```python
# backend/app/services/ai/clarification.py

FALLBACK_TEMPLATES = [
    {
        "keywords": ["完成", "学完", "进度"],
        "rephrases": [
            ("查询{scope}各院系的课件完成率", "COMPLETION_RATE_QUERY"),
            ("查询{scope}未完成学习的学员名单", "INCOMPLETE_LEARNER_QUERY"),
            ("查询{scope}学习进度的整体概况", "LEARNING_PROGRESS_QUERY"),
        ],
    },
    {
        "keywords": ["考试", "成绩", "分数", "通过"],
        "rephrases": [
            ("查询{scope}各院系的考试通过率", "EXAM_PASS_RATE_QUERY"),
            ("查询{scope}考试成绩排名情况", "PERFORMANCE_RANKING_QUERY"),
            ("查询{scope}考试中错误率最高的题目", "SKILL_ERROR_QUERY"),
        ],
    },
    # ... 更多关键词组合
]
```

**处理流程:**

```
LLM 主路径失败 -> LLM 降级失败
  |
  v
ClarificationService.generate_options(question, user_ctx)
  |
  +-- 匹配关键词 -> 生成 3 个转述选项（每个绑定 intent）
  +-- 无匹配 -> 使用默认模板（完成率相关）
  |
  v
返回 SSE 事件: clarification_options
  {
    "options": [
      {"index": 1, "text": "查询本月各院系的课件完成率", "intent": "COMPLETION_RATE_QUERY"},
      {"index": 2, "text": "查询本月未完成学习的学员名单", "intent": "INCOMPLETE_LEARNER_QUERY"},
      {"index": 3, "text": "查询本月学习进度的整体概况", "intent": "LEARNING_PROGRESS_QUERY"}
    ]
  }
```

**用户响应:**

- 选 1/2/3 -> 直接使用对应 intent+slots 继续 ReAct 流程
- 选 "都不是" -> 原问题写入 `doc/unmatched_queries.md`

### 5.4 超时与模型配置

| 指标 | 主路径 | 降级 |
|------|--------|------|
| 超时 | 5s | 8s |
| LLM 模型 | `LLM_LIGHT_MODEL` (from config, 默认 qwen2.5-7b-instruct) | 同 |
| temperature | 0.1 | 0.15 |

### 5.5 Config 新增字段

```python
# backend/app/core/config.py
LLM_BASE_URL: str = "http://localhost:8000/v1"
LLM_API_KEY: str = "not-needed"
LLM_LIGHT_MODEL: str = "qwen2.5-7b-instruct"    # Phase 3 意图识别用
LLM_HEAVY_MODEL: str = "qwen2.5-72b-instruct"   # Phase 5 ReAct 用
```

---

## 6. 新增 API 端点

### 6.1 POST /api/v1/ai-query/clarify

请求 LLM 意图识别失败时 SSE 推送的选项。正常情况下用户不直接调用此端点。

### 6.2 POST /api/v1/ai-query/clarify/select

```
Body: {"question_index": 1}   -- 用户选了第 1 个转述
Body: {"question_index": -1, "original_question": "..."}   -- "都不是"
```

- 选 1-3: 用对应 intent+slots 继续后续 ReAct 流程
- 选 -1: 保存到 `doc/unmatched_queries.md`，返回 "问题已记录，我们会尽快改进"

### 6.3 doc/unmatched_queries.md 格式

```markdown
# 未匹配的用户问题

| 时间 | 用户 | 角色 | 问题 |
|------|------|------|------|
| 2026-06-12 14:30 | 张三 | admin | 最近学习情况怎么样 |
```

---

## 7. 测试策略

### 7.1 单元测试（10 个，不依赖 LLM）

| # | 测试 | 验证点 |
|---|------|--------|
| 1 | test_intent_result_valid | 完整 JSON -> model_validate_json 成功 |
| 2 | test_intent_result_missing_field | 缺字段 -> 验证失败 |
| 3 | test_intent_result_invalid_intent | 意图不在 22 个中 -> 失败 |
| 4 | test_slot_values_defaults | 默认值正确 |
| 5 | test_json_schema_generation | schema 含 intent enum 约束 |
| 6 | test_22_intents_complete | INTENT_DEFINITIONS 长度 = 22 |
| 7 | test_no_duplicate_intents | 22 个 intent 无重复 |
| 8 | test_dynamic_context_build | 用户上下文注入正确 |
| 9 | test_fallback_on_schema_failure | Mock 主路径异常 -> 自动走降级 |
| 10 | test_classification_error_triggers_clarify | 双层失败 -> 触发 ClarificationService |

### 7.2 集成测试（对真实 LLM，单独运行）

| # | 测试 | 验证点 |
|---|------|--------|
| 1 | 22 意图各 2-3 个变体 | 整体正确率 >= 92% |
| 2 | 模拟超时（timeout=0.001s） | 降级触发 |
| 3 | 模糊问题 | need_clarification=true |
| 4 | 关键词匹配追问 | 3 个选项正确生成 |

### 7.3 验收标准

| 指标 | 要求 |
|------|------|
| 单元测试 | 10/10 通过 |
| 意图分类准确率 | >= 92% |
| 主路径响应时间 | < 1.0s |
| 降级路径响应时间 | < 3.0s |
| 追问选项相关性 | 至少 1 个选项匹配用户意图（人工抽检 20 条） |

---

## 8. 不纳入 Phase 3

- ReAct 推理引擎 -> Phase 5
- SSE 问答端点 /api/v1/ai-query -> Phase 5
- 工具集 (16 tools) -> Phase 4
- 前端 Chat UI -> Phase 6
