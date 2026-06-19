"""Build the system prompt for intent classification."""
from datetime import datetime
from app.schemas.auth import UserContext
from app.services.ai.intent_definitions import get_intent_list_for_prompt

# Role level mapping: 0=highest privilege, 3=lowest
_ROLE_LABELS = {0: "超级管理员 (SuperAdmin)", 1: "管理员 (Admin)", 2: "教师 (Teacher)", 3: "学生 (Student)"}
_ROLE_SCOPES = {0: "org", 1: "org", 2: "dept", 3: "individual"}


def role_label(role_level: int) -> str:
    """Human-readable role name for LLM prompts."""
    return _ROLE_LABELS.get(role_level, f"未知角色({role_level})")


def role_default_scope(role_level: int) -> str:
    """Default scope_type based on role: org|dept|individual."""
    return _ROLE_SCOPES.get(role_level, "individual")

ROLE_DECLARATION = """You are the intent classification engine for the SkillCloudHS training data analysis system.
Your ONLY job is to classify user questions and extract query parameters.
Do NOT try to answer the question. Only output structured JSON."""

SLOT_EXTRACTION_RULES = """## Slot Extraction Rules

time_range: Output as a JSON object, NOT a string:
  - today → {"type": "today"}
  - this week → {"type": "this_week"}
  - this month → {"type": "this_month"}
  - last month → {"type": "last_month"}
  - this quarter → {"type": "this_quarter"}
  - this year → {"type": "this_year"}
  - last N days/weeks/months → {"type": "custom", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

scope_type:
  - Role levels (lower = higher privilege): 0=SuperAdmin(全机构) 1=Admin(本机构) 2=Teacher(本部门) 3=Student(仅本人)
  - Default scope based on user's role: SuperAdmin/Admin -> org, Teacher -> dept, Student -> individual
  - User explicitly mentions a scope -> use that instead of default
  - mentions class -> class | mentions a person's name -> individual

IMPORTANT: If the question contains "why" or "reason" words, force complexity=complex.
IMPORTANT: If the question is vague (e.g., "how is everything going"), set need_clarification=true.

DISAMBIGUATION HINTS (use correct intent):
  - "completion_rate" (完成率, coursework done %) vs "pass_rate" (通过率, is_passed=1 ratio)
  - "course count" (课程数量) vs "exam count" (考试场次数量) vs "user count" (用户数量)
  - "class query" (班级学生查询, needs M1+M2) vs "org overview" (机构概览, needs M9+M10)
  - "how many students/teachers" -> ROLE_COUNT_QUERY (not ORG_OVERVIEW_QUERY)
  - "what classes in dept X" -> ORG_STRUCTURE_QUERY (not ORG_OVERVIEW_QUERY)
  - "list students in class Y" -> CLASS_STUDENT_QUERY
  - "how many courses" -> COURSE_COUNT_QUERY"""

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
        rl = role_label(user_ctx.role_level)
        rs = role_default_scope(user_ctx.role_level)
        dynamic = f"""## Current Context
User: {user_ctx.user_name}
Role: {rl} (level={user_ctx.role_level}), dept={user_ctx.dept_code or "N/A"}
Default scope for this user: {rs}
Time: {now}

{module_index_text}"""

        return "\n\n".join([
            ROLE_DECLARATION,
            dynamic,
            self._intent_table,
            SLOT_EXTRACTION_RULES,
            OUTPUT_INSTRUCTION,
        ])
