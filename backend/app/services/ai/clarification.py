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
        "keywords": [r"学.*多久", "时长", "时间", r"花.*小时"],
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
                "|------|------|------|----------|\n",
                encoding="utf-8",
            )

        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
