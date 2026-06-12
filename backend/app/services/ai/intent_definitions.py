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
