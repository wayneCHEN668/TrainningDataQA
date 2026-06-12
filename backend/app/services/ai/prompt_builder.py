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
