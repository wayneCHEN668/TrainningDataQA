"""ReAct reasoning engine wrapping LangChain agent with SSE event streaming."""
import asyncio
import logging
import time
from typing import AsyncGenerator
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.schemas.auth import UserContext
from app.schemas.sse_events import SSEEvent

logger = logging.getLogger(__name__)

MAX_STEPS = 8
MAX_LLM_RETRIES = 2

REACT_SYSTEM_TEMPLATE = """You are the intelligent analysis engine for the SkillCloudHS training data analysis system.
Answer user questions about training data through Thought -> Action -> Observation cycles.

## Current User
Name: {user_name}
Role: level={role_level}, dept={dept_code}
Current time: {current_time}

## Recent Conversation
{chat_history}

## User Question
{input}

## Intent Classification Result
{intent_info}

## Available Data Tables (only query these)
{schema_context}

## Available Tools
{tools}

## ReAct Format (strictly follow)
Thought: [analyze what you know, what's missing, what to do next]
Action: [tool name]
Action Input: [JSON parameters]
Observation: [tool result]
... (repeat, max 8 steps)
Thought: [confirm you have enough information]
Final Answer: [natural language answer for the user, with data evidence and recommendations]

## Constraints
1. ONLY query tables listed in "Available Data Tables" above
2. ALL numbers must come from tool results -- never invent data
3. When user mentions a course/exam name, call search_course_or_exam FIRST to resolve the code
4. Mark important numbers with **number** format
5. Declare only ONE Action at a time"""


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
    ):
        self._llm = ChatOpenAI(
            model=llm_model,
            base_url=llm_base_url,
            api_key="not-needed",
            temperature=0.2,
            streaming=True,
        )
        self._tools = tools
        self._schema_context = schema_context
        self._user_ctx = user_ctx
        self._history = chat_history or []

    async def run(
        self, question: str, intent_result
    ) -> AsyncGenerator[SSEEvent, None]:
        """Run ReAct loop and yield SSE events."""
        system_prompt = self._build_system_prompt(question, intent_result)

        limiter = ToolCallLimitMiddleware(
            run_limit=MAX_STEPS,
            exit_behavior="end",
        )
        agent = create_agent(
            self._llm,
            tools=self._tools,
            system_prompt=system_prompt,
            middleware=[limiter],
        )

        retries = 0
        while retries <= MAX_LLM_RETRIES:
            try:
                step_no = 0
                async for chunk in agent.astream_events(
                    {"messages": [HumanMessage(content=question)]},
                    version="v2",
                ):
                    event_type = chunk.get("event", "")
                    if event_type == "on_tool_start":
                        step_no += 1
                        inp = chunk["data"].get("input", {})
                        yield SSEEvent(
                            type="step_start",
                            data={
                                "step_no": step_no,
                                "thought": "",
                                "action": chunk.get("name", ""),
                                "params_summary": _summarize_params(inp),
                            },
                        )
                    elif event_type == "on_tool_end":
                        output = chunk["data"].get("output", "")
                        yield SSEEvent(
                            type="step_done",
                            data={
                                "step_no": step_no,
                                "tool_name": chunk.get("name", ""),
                                "result_summary": _summarize_result(output),
                            },
                        )
                    elif event_type == "on_chat_model_stream":
                        delta = chunk["data"]["chunk"].content
                        if delta:
                            yield SSEEvent(
                                type="answer_chunk", data={"text_delta": delta}
                            )
                return  # Success

            except Exception as e:
                retries += 1
                if retries > MAX_LLM_RETRIES or not _is_retryable(e):
                    yield SSEEvent(
                        type="error",
                        data={
                            "code": "LLM_CALL_FAILED",
                            "message": f"AI service error: {e}",
                            "recoverable": False,
                        },
                    )
                    return
                await asyncio.sleep(2 ** retries)

    def _build_system_prompt(self, question: str, intent_result) -> str:
        """Build the full system prompt from template parts."""
        history_text = self._format_history()
        intent_text = (
            f"intent={intent_result.intent}, "
            f"complexity={intent_result.complexity}"
        )
        return REACT_SYSTEM_TEMPLATE.format(
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
