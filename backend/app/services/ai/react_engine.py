"""ReAct reasoning engine with manual text-parsing and SSE event streaming."""
import asyncio
import json
import logging
import re
import time
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.schemas.auth import UserContext
from app.schemas.sse_events import SSEEvent
from app.services.ai.schema_index import SchemaIndexService

logger = logging.getLogger(__name__)

MAX_STEPS = 8
MAX_LLM_RETRIES = 2
DEFAULT_LLM_TIMEOUT = 60.0

REACT_SYSTEM_TEMPLATE = """你是 SkillCloudHS 培训数据分析系统的智能分析引擎。
通过 Thought -> Action -> Action Input -> Observation 循环回答用户问题。

## 当前用户
姓名: {user_name}
角色: level={role_level}, 部门={dept_code}
当前时间: {current_time}

## 权限与范围说明
你的角色级别决定了查询范围，系统会自动注入 WHERE 条件进行数据过滤，你无需手动限制权限：
- level=0 (超级管理员): 可查看全机构数据，工具中的 scope_type 参数使用 "all" 或 "org"
- level=1 (管理员): 可查看本机构数据，scope_type 使用 "org" 或 "dept"
- level=2 (教师): 可查看本部门/班级数据，scope_type 使用 "dept" 或 "class"
- level=3 (学生): 仅可查看个人数据，scope_type 使用 "user"

重要提示：
- scope_type 仅用于引导统计维度（按机构/部门/班级/个人分组），不控制实际权限
- 你当前的角色是 level={role_level}，请根据上述规则选择合适的 scope_type
- 系统会根据你的角色自动过滤数据，你凭 scope_type="all" 查询也不会看到无权访问的数据

## 最近对话
{chat_history}

## 用户问题
{input}

## 意图分类结果
{intent_info}

## 可用数据表
{schema_context}

## 可用工具
{tools}

## 回答流程（严格遵循）
Thought: [分析问题，确定需要哪个工具]
Action: [工具名称，从上面列表中选择]
Action Input: [JSON参数，如 {{'key': 'value'}}]
Observation: [系统会自动填入工具返回的数据]

如果需要多个步骤，继续:
Thought: [分析Observation的数据，确定下一步]
Action: [下一个工具名称]
Action Input: [JSON参数]
Observation: [系统自动填入]

当信息足够时，必须严格按照以下格式给出最终回答：
Thought: 我已获得足够数据
Final Answer: [用中文自然语言回答，包含数据和图表]

**重要**：最终回答正文前必须包含 "Final Answer:" 前缀标记，不得省略。如果省略该标记，系统将无法识别你的回答并丢弃全部内容。

## 回答格式要求
1. **数据解读**：用中文自然语言解释查询到的数据，说明关键数字的含义和趋势
2. **文本优先**：即使生成了图表，也必须提供文字形式的答案。图表是文字的补充，不能替代文字
3. **具体要求**：如果用户问"列出"、"有哪些"、"前N名"，必须在文字中逐条列出
4. **图表**：如果数据适合可视化，使用 ![图表标题](chart_id) 格式，chart_id 必须是 generate_chart_spec 返回的确切 ID
5. **图表解读**：在图表占位符后，用中文解释图表展示的内容和洞察

示例回答：
根据查询结果，2024年Q1的培训完成情况如下：

- 总培训人数：**1,234人**
- 完成率：**87.5%**，较上季度提升 **3.2个百分点**
- 未通过人数：**45人**，主要集中在技术部门

![2024年Q1培训完成率趋势](chart_abc123)

从图表可以看出，1月至3月的完成率呈上升趋势，其中3月达到最高点 **91.2%**。建议继续保持当前的培训策略，并针对技术部门加强辅导。

## 概念区分（必须记住！）
- **完成率 (completion_rate)**：学员完成了多少课件的百分比（0-100%）。不等于"通过"。
- **通过率 (pass_rate)**：is_passed=1 的人数占总人数的比例。用户问"通过率"时必须用 is_passed 字段，不要用 completion_rate。
- **course_grade 表的记录数 != 用户总数**：一个用户可能有多门课程的成绩记录。用户总数应从 user_info 表统计。
- 当用户要求"列出"或"前N名"时，必须在回答文本中列出名称和数值，不能仅放在图表中。

## 约束条件
1. 仅查询上方"可用数据表"中列出的表
2. 所有数字必须来自本次工具查询结果——绝不编造数据
3. 当用户提到课程/考试名称时，先调用 search_course_or_exam 解析代码
4. 用 **数字** 格式标记重要数字
5. 回答必须用中文撰写，包含对数据的自然语言解释
6. 如果生成了图表，使用 ![标题](chart_id) 格式引用，chart_id 必须是 generate_chart_spec 返回的确切 ID
7. 每个数据统计问题必须至少调用一次工具查询数据库，不得凭上下文直接回答
8. 即使生成了图表，也必须提供文字形式的答案
9. 最终回答正文之前必须写上 "Final Answer:" 作为标记，否则系统无法识别你的回答
"""

REPORT_MODE_APPENDIX = """## 报表模式
用户需要生成可下载的Excel报表。请：
1. 优先使用能返回表格数据的工具（如 query_completion_rate、query_exam_performance 等）
2. 在最终回答中概述报表内容（包含哪些数据、大概行数）
3. 在回答末尾提示用户："报表已生成，请从右侧面板下载Excel文件"
4. 回答保持简洁——详细数据在Excel中，这里只需给出关键统计结论"""


class ReactEngine:
    """Wraps LangChain agent for SSE-streamed ReAct reasoning."""

    def __init__(
        self,
        llm_base_url: str,
        llm_model: str,
        schema_context: str,
        user_ctx: UserContext,
        tools: list,
        chat_history: list[dict] | None = None,
        llm_api_key: str | None = None,
        schema_svc: SchemaIndexService | None = None,
    ):
        self._llm = ChatOpenAI(
            model=llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key or "not-needed",
            temperature=0,  # P0 fix: deterministic output for stability
            streaming=True,
        )
        self._tools = tools
        self._schema_context = schema_context
        self._user_ctx = user_ctx
        self._history = chat_history or []
        self._schema_svc = schema_svc

    @staticmethod
    async def _stream_with_timeout(stream, timeout: float = DEFAULT_LLM_TIMEOUT) -> str:
        """Collect an async LLM stream with a hard timeout to avoid hanging forever."""
        async def _collect() -> str:
            result = ""
            async for chunk in stream:
                delta = chunk.content if hasattr(chunk, "content") else str(chunk)
                if delta:
                    result += delta
            return result
        return await asyncio.wait_for(_collect(), timeout=timeout)

    async def run(
        self, question: str, intent_result, output_mode: str = "analysis"
    ) -> AsyncGenerator[SSEEvent, None]:
        """Manual ReAct loop — parse text Action/Input, execute tools, stream SSE."""
        system_prompt = self._build_system_prompt(question, intent_result, output_mode)
        tool_by_name = {t.name: t for t in self._tools}
        self._tool_results: list[dict] = []

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=question)]
        answer_buffer = ""
        chart_ids = set()
        final_text = ""

        for step_no in range(1, MAX_STEPS + 1):
            # Call LLM
            retries = 0
            llm_output = ""
            while retries <= MAX_LLM_RETRIES:
                try:
                    stream = self._llm.astream(messages)
                    llm_output = await self._stream_with_timeout(stream)
                    answer_buffer += llm_output
                    break
                except asyncio.TimeoutError:
                    print(f"[ReactEngine] LLM 调用超时 (step={step_no}, retry={retries})", flush=True)
                    retries += 1
                    if retries > MAX_LLM_RETRIES:
                        yield SSEEvent(type="error", data={
                            "code": "LLM_TIMEOUT",
                            "message": "AI 服务响应超时，请稍后重试。",
                            "recoverable": True,
                        })
                        return
                    await asyncio.sleep(2 ** retries)
                except Exception as exc:
                    if not _is_retryable(exc):
                        yield SSEEvent(type="error", data={
                            "code": "LLM_CALL_FAILED",
                            "message": f"AI service error: {exc}",
                            "recoverable": False,
                        })
                        return
                    retries += 1
                    if retries > MAX_LLM_RETRIES:
                        yield SSEEvent(type="error", data={
                            "code": "LLM_RETRY_EXHAUSTED",
                            "message": f"AI service unavailable: {str(exc)[:100]}",
                            "recoverable": True,
                        })
                        return
                    await asyncio.sleep(2 ** retries)

            # Check for Final Answer (support English + Chinese variants)
            fa_match = re.search(
                r"(?:Final Answer|最终回答|最终答案|答案)[:：]\s*(.+)",
                llm_output, re.DOTALL | re.IGNORECASE
            )
            if fa_match:
                final_text = fa_match.group(1).strip()
                if final_text:
                    yield SSEEvent(type="answer_chunk", data={"text_delta": "\n" + final_text})
                    answer_buffer += "\n" + final_text
                break

            # Parse Action — use \w+ to avoid capturing trailing () or other chars
            print(f"[ReactEngine] step={step_no}, parsing llm_output ({len(llm_output)} chars): {llm_output[:200]}", flush=True)
            action_match = re.search(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)", llm_output)
            if not action_match:
                print(f"[ReactEngine] 未找到 Action, 退出循环", flush=True)
                break

            tool_name = action_match.group(1).strip()
            tool = tool_by_name.get(tool_name)
            action_input_str = ""
            # Parse Action Input using bracket-matching for robust JSON extraction
            # (handles arbitrary nesting depth, unlike the old regex)
            action_input_str = _extract_action_input(llm_output)

            if not tool:
                observation = f"Error: tool '{tool_name}' not found. Available: {list(tool_by_name.keys())}"
            else:
                try:
                    tool_input = json.loads(action_input_str) if action_input_str else {}
                except json.JSONDecodeError:
                    observation = f"Error: invalid JSON: {action_input_str[:200]}"
                    tool_input = None

                if tool_input is not None:
                    try:
                        # Extract thought text from the raw LLM output
                        thought_match = re.search(
                            r"Thought:\s*(.+?)(?=\n(?:Action|Observation|Final)|\Z)",
                            llm_output, re.DOTALL | re.IGNORECASE
                        )
                        thought_text = thought_match.group(1).strip() if thought_match else ""
                        yield SSEEvent(type="step_start", data={
                            "step_no": step_no, "thought": thought_text,
                            "action": tool_name,
                            "params_summary": _summarize_params(tool_input),
                        })
                        result = await tool.ainvoke(tool_input)
                        observation = json.dumps(result, ensure_ascii=False, default=str)
                        self._tool_results.append({
                            "tool_name": tool_name,
                            "result": result,
                        })

                        chart_data = _extract_chart_data(result)
                        if chart_data:
                            chart_ids.add(chart_data["chart_id"])
                            yield SSEEvent(type="chart_ready", data={
                                "chartId": chart_data["chart_id"],
                                "chartType": chart_data.get("chart_type", "bar"),
                                "title": chart_data.get("title", ""),
                                "rechartsSpec": chart_data.get("recharts_spec", {}),
                            })
                        yield SSEEvent(type="step_done", data={
                            "step_no": step_no, "tool_name": tool_name,
                            "result_summary": _summarize_result(observation),
                        })
                    except Exception as e:
                        observation = f"Error executing tool: {str(e)}"

            # Feed Observation back — append to internal buffer but do NOT
            # stream as answer_chunk (it's the ReAct trace, not the answer).
            obs_text = f"\nObservation: {observation}\n"
            answer_buffer += obs_text
            messages.append(AIMessage(content=llm_output))
            messages.append(HumanMessage(content=f"Observation: {observation}"))

        # ── Post-process: handle various answer quality issues ────        # ── Post-process: handle various answer quality issues ──────────────────

        # Case 1: Completely empty — LLM produced nothing at all
        if not answer_buffer.strip() and not chart_ids:
            print("[ReactEngine] 警告: LLM 未产生任何输出, 可能 API 返回空响应", flush=True)
            yield SSEEvent(
                type="error",
                data={
                    "code": "EMPTY_RESPONSE",
                    "message": "AI 未产生回复，请稍后重试。如持续出现，可能需要检查 LLM 服务状态。",
                    "recoverable": True,
                },
            )
            return

        # Try to extract a structured Final Answer
        final_answer = _extract_final_answer(answer_buffer)

        if final_answer:
            # Case 2: Explicit Final Answer found — nothing more to do
            pass
        else:
            # Case 3: No "Final Answer:" marker — try fallback extraction
            fallback = _extract_final_answer_from_buffer(answer_buffer)

            if fallback and len(fallback.strip()) > 10:
                # Found meaningful content after Observations — yield it
                print(f"[ReactEngine] 从缓冲区提取回答文本 ({len(fallback)} 字符)", flush=True)
                yield SSEEvent(
                    type="answer_chunk",
                    data={"text_delta": fallback}
                )
            elif chart_ids:
                # Charts exist but no text answer — inject chart placeholders with
                # a minimal explanation so the user isn't left with silence
                print("[ReactEngine] 仅有图表无文本回答, 注入图表占位符", flush=True)
                chart_placeholders = "\n\n".join(
                    f"![数据图表]({cid})" for cid in chart_ids
                )
                yield SSEEvent(
                    type="answer_chunk",
                    data={
                        "text_delta": f"\n\n根据查询结果，数据可视化如下：\n\n{chart_placeholders}"
                    },
                )
            else:
                # Nothing recoverable — report to user with a recoverable error
                print(f"[ReactEngine] 未能提取回答, buffer预览({len(answer_buffer)} chars): {answer_buffer[:200]}", flush=True)
                yield SSEEvent(
                    type="error",
                    data={
                        "code": "NO_ANSWER_EXTRACTED",
                        "message": "AI 完成了思考步骤但未生成文本回答。请尝试重新提问或简化问题。",
                        "recoverable": True,
                    },
                )
                return

    def _build_system_prompt(self, question: str, intent_result, output_mode: str = "analysis") -> str:
        """Build the full system prompt from template parts."""
        history_text = self._format_history()
        intent_text = (
            f"intent={intent_result.intent}, "
            f"complexity={intent_result.complexity}"
        )
        base = REACT_SYSTEM_TEMPLATE.format(
            user_name=self._user_ctx.user_name,
            role_level=self._user_ctx.role_level,
            dept_code=self._user_ctx.dept_code or "N/A",
            current_time=time.strftime("%Y-%m-%d %H:%M"),
            chat_history=history_text,
            input=question,
            schema_context=self._schema_context,
            tools=self._format_tools(),
            intent_info=intent_text,
        )
        if output_mode == "report":
            base += "\n\n" + REPORT_MODE_APPENDIX
        return base

    def _format_history(self) -> str:
        if not self._history:
            return "(no previous conversation)"
        lines = []
        for h in self._history:
            role = "User" if h["role"] == "user" else "AI"
            lines.append(f"{role}: {h['content']}")
        return "\n".join(lines)

    def _format_tools(self) -> str:
        lines = []
        for t in self._tools:
            lines.append(f"- {t.name}: {t.description}")
        return "\n".join(lines)


# Patterns that indicate non-answer system/error text
_ERROR_PATTERNS = [
    r"^\d+\s+validation errors?\b",          # Pydantic: "1 validation error for ..."
    r"^Field required\b",                     # Pydantic field error
    r"^For further information visit\b",      # Pydantic error footer
    r"^Error executing tool:",                # Tool execution error
    r"^Error: invalid JSON",                  # JSON parse error
    r"^Error: tool ",                         # Tool not found error
    r"^\w+\n\s*Field required",              # Multi-line Pydantic start
]

# Patterns that indicate LLM internal reasoning leaked into answer text
_REASONING_PATTERNS = [
    r"首先构造合并数据",
    r"手动合并[：:]",
    r"然后生成图表",
    r"将.*data.*按.*合并",
    r"将两个查询结果",
]

def _looks_like_error(text: str) -> bool:
    """Check if text looks like an error message rather than an answer."""
    for pattern in _ERROR_PATTERNS:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False


def _strip_reasoning(text: str) -> str:
    """Remove LLM internal reasoning fragments from answer text."""
    for pattern in _REASONING_PATTERNS:
        # Remove the reasoning sentence (up to next period or newline)
        text = re.sub(r"[^。\n]*?" + pattern + r"[^。\n]*[。\n]\s*", "", text)
    return text.strip()


def _extract_final_answer(text: str) -> str:
    """Extract answer content from the full response text.

    Handles both old ReAct format (Final Answer: marker) and new
    tool-calling agent format (plain text after tool calls).
    """
    # Try old ReAct format first — capture only until next ReAct marker
    match = re.search(
        r"Final Answer:\s*((?:(?!\n(?:Thought|Action|Action Input|Observation|Final\s*Answer):).)+)",
        text, re.DOTALL | re.IGNORECASE
    )
    if match:
        result = match.group(1).strip()
        if result and not _looks_like_error(result):
            return _strip_reasoning(result)
    # New format: answer is the text content without tool-call markers
    # Strip out ReAct traces if present, return remaining content
    cleaned = re.sub(
        r"^(Thought|Action|Action Input|Observation):.*$",
        "",
        text,
        flags=re.MULTILINE
    ).strip()
    # Filter out error-looking lines
    lines = cleaned.split("\n")
    answer_lines = [l for l in lines if not _looks_like_error(l)]
    cleaned = "\n".join(answer_lines).strip()
    return _strip_reasoning(cleaned) if len(cleaned) > 10 else ""


def _extract_final_answer_from_buffer(buffer: str) -> str:
    """Extract meaningful content when Final Answer marker is missing.

    Uses a layered strategy:
    1. Content after the last Observation (filtered for errors)
    2. Chinese text segments containing data-related keywords
    3. Last non-ReAct lines as final fallback
    """
    # Strategy 1: Find content after last Observation
    obs_matches = list(re.finditer(
        r"Observation:.*?\n(.*?)(?=Thought:|Action:|Observation:|$)",
        buffer, re.DOTALL
    ))
    if obs_matches:
        content = obs_matches[-1].group(1).strip()
        lines_out = []
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            if re.match(
                r"^(Thought|Action|Action Input|Observation|Final\s*Answer):",
                line
            ):
                continue
            if _looks_like_error(line):
                continue
            lines_out.append(line)
        if lines_out:
            result = "\n".join(lines_out)
            if not _looks_like_error(result):
                return _strip_reasoning(result)

    # Strategy 2: Find Chinese text segments containing data keywords
    chinese_segments = re.findall(
        r"[\u4e00-\u9fff]{4,}.*?(?:数据|结果|完成|通过|人数|率|分|趋势|统计|学员|课程|平均|总分|分钟|活跃)",
        buffer
    )
    if chinese_segments:
        filtered = [s for s in chinese_segments if not _looks_like_error(s)]
        if filtered:
            return _strip_reasoning("\n".join(filtered[-3:]))

    # Strategy 3: Return last non-ReAct, non-error lines (up to 5)
    all_lines = buffer.split("\n")
    content_lines = [
        l.strip() for l in all_lines
        if l.strip()
        and not re.match(r"^(Thought|Action|Action Input|Observation|Final):", l.strip())
        and not _looks_like_error(l.strip())
    ]
    if content_lines:
        return _strip_reasoning("\n".join(content_lines[-5:]))

    return ""
def _summarize_params(params: dict) -> str:
    """Brief summary of tool parameters for SSE display."""
    if not isinstance(params, dict):
        return ""
    parts = []
    for k, v in params.items():
        if k.startswith("_"):
            continue
        if isinstance(v, list) and len(v) > 3:
            v = v[:3]
        s = str(v)
        if len(s) > 40:
            s = s[:37] + "..."
        parts.append(f"{k}={s}")
    return ", ".join(parts) if parts else ""


def _summarize_result(result) -> str:
    """Brief summary of tool result for SSE display."""
    if isinstance(result, dict):
        keys = [
            "completion_rate", "pass_rate", "count", "total",
            "avg_score", "anomalies", "level", "matches", "error_rate",
        ]
        parts = []
        for k in keys:
            if k in result:
                v = result[k]
                if isinstance(v, (int, float)):
                    parts.append(f"{k}={v}")
                elif isinstance(v, list):
                    parts.append(f"{k}=[{len(v)} items]")
        if parts:
            return ", ".join(parts[:4])
        return f"Result with {len(result)} fields"
    s = str(result)
    return s[:120] + "..." if len(s) > 120 else s


def _is_retryable(exc: Exception) -> bool:
    name = type(exc).__name__
    return any(kw in name for kw in ("Timeout", "Connection", "RateLimit"))


def _extract_chart_data(output) -> dict | None:
    """Extract chart data from tool output, normalizing various LangChain formats.

    LangChain astream_events v2 may return tool output as:
    - Raw dict (ideal)
    - ToolMessage object (has .content attribute)
    - JSON string
    - AI Message with .content
    """
    import json as _json

    # 1. Already a dict with chart_id
    if isinstance(output, dict) and "chart_id" in output:
        return output

    # 2. Object with .content (ToolMessage / AIMessage)
    content = getattr(output, "content", None)
    if content is not None:
        if isinstance(content, dict) and "chart_id" in content:
            return content
        if isinstance(content, str):
            try:
                parsed = _json.loads(content)
                if isinstance(parsed, dict) and "chart_id" in parsed:
                    return parsed
            except (_json.JSONDecodeError, TypeError):
                pass

    # 3. Plain string (JSON)
    if isinstance(output, str):
        try:
            parsed = _json.loads(output)
            if isinstance(parsed, dict) and "chart_id" in parsed:
                return parsed
        except (_json.JSONDecodeError, TypeError):
            pass

    return None


def _extract_action_input(llm_output: str) -> str:
    """Extract Action Input JSON from LLM output using bracket-matching.

    This replaces the fragile regex approach and correctly handles
    arbitrarily nested JSON objects/arrays that the old regex could not.

    Strategy:
    1. Find "Action Input:" marker (case-insensitive)
    2. Scan forward for the first { or [ character
    3. Use bracket-matching to find the complete balanced JSON string
    """
    # Find the Action Input marker
    marker_match = re.search(
        r"Action\s*Input\s*[:：]\s*",
        llm_output,
        re.IGNORECASE
    )
    if not marker_match:
        return ""

    # Start scanning after the marker
    pos = marker_match.end()

    # Find the first opening bracket
    while pos < len(llm_output) and llm_output[pos] not in "{[":
        pos += 1
    if pos >= len(llm_output):
        return ""

    opening = llm_output[pos]
    closing = "}" if opening == "{" else "]"

    # Bracket-matching: track depth, respect string literals
    depth = 0
    in_string = False
    escape = False
    start = pos

    while pos < len(llm_output):
        ch = llm_output[pos]
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
            elif ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return llm_output[start:pos + 1]
        pos += 1

    # Unbalanced brackets — return what we have (best effort)
    return llm_output[start:]
