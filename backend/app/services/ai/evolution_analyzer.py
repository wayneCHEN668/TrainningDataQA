"""QA log analyzer for daily evolution reports."""
import re
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Path relative to this file: backend/app/services/ai/ -> project_root/doc/unmatched_queries.md
UNMATCHED_QUERIES_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "doc" / "unmatched_queries.md"

LOW_QUALITY_RULES = {
    "negative_feedback": "user_feedback = -1",
    "fallback_used": "fallback_used = 1",
    "too_many_steps": "steps_count >= 7",
    "too_slow": "duration_ms > 30000",
}


@dataclass
class OverallMetrics:
    total_qa: int = 0
    avg_duration_ms: float = 0
    avg_tokens: float = 0
    low_quality_rate: float = 0
    satisfaction_rate: float = 0
    daily_trend: list[dict] = field(default_factory=list)


@dataclass
class IntentStat:
    intent: str
    count: int
    pct: float
    low_quality_rate: float
    avg_duration_ms: float


@dataclass
class UnmatchedSummary:
    total_new_this_week: int
    total_accumulated: int
    top_patterns: list[str]


@dataclass
class EvolutionReport:
    period_days: int
    generated_at: str
    overall: OverallMetrics
    intent_distribution: list[IntentStat]
    low_quality_items: list[dict]
    unmatched: UnmatchedSummary

    def to_summary_json(self) -> str:
        import json
        return json.dumps({
            "period_days": self.period_days,
            "generated_at": self.generated_at,
            "overall": {
                "total_qa": self.overall.total_qa,
                "avg_duration_ms": self.overall.avg_duration_ms,
                "low_quality_rate": self.overall.low_quality_rate,
            },
            "top_intents": [
                {"intent": s.intent, "count": s.count}
                for s in self.intent_distribution[:10]
            ],
            "unmatched_new": self.unmatched.total_new_this_week,
            "unmatched_total": self.unmatched.total_accumulated,
        }, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines = [
            f"# SkillCloudHS Evolution Report",
            f"",
            f"**Date**: {self.generated_at}  |  **Period**: past {self.period_days} days",
            f"",
            f"## S1 Overall Metrics",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Q&A | {self.overall.total_qa} |",
            f"| Avg Duration (ms) | {self.overall.avg_duration_ms:.0f} |",
            f"| Avg Tokens | {self.overall.avg_tokens:.0f} |",
            f"| Low Quality Rate | {self.overall.low_quality_rate:.1%} |",
            f"| Satisfaction Rate | {self.overall.satisfaction_rate:.1%} |",
            f"",
            f"## S2 Intent Distribution (Top 10)",
            f"",
            f"| Intent | Count | Share | Low Quality | Avg Duration |",
            f"|--------|-------|-------|-------------|-------------|",
        ]
        for s in self.intent_distribution[:10]:
            flag = " **HIGH**" if s.low_quality_rate > 0.2 else ""
            lines.append(
                f"| {s.intent} | {s.count} | {s.pct:.1%} | {s.low_quality_rate:.1%}{flag} | {s.avg_duration_ms:.0f}ms |"
            )
        lines += [
            f"",
            f"## S3 Unmatched Queries",
            f"",
            f"| Type | Count |",
            f"|------|-------|",
            f"| New this week | {self.unmatched.total_new_this_week} |",
            f"| Accumulated total | {self.unmatched.total_accumulated} |",
            f"",
        ]
        if self.unmatched.top_patterns:
            lines.append("**Common patterns**:")
            for p in self.unmatched.top_patterns:
                lines.append(f"- {p}")
        lines += [
            f"",
            f"## S4 Improvement Suggestions",
            f"",
        ]
        for s in self.intent_distribution[:10]:
            if s.low_quality_rate > 0.2:
                lines.append(f"- **[TEMPLATE] {s.intent}**: low quality rate {s.low_quality_rate:.1%}, consider optimizing ReAct prompt or tool descriptions")
        if self.unmatched.top_patterns:
            lines.append(f"- **[NEW INTENT]**: Top patterns from unmatched queries may need new intent types or keyword rules")
        return "\n".join(lines)


class EvolutionAnalyzer:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def analyze(self, days: int = 7) -> EvolutionReport:
        overall = await self._query_overall_metrics(days)
        intent_stats = await self._query_intent_distribution(days)
        low_quality = await self._query_low_quality(days)
        unmatched = self._parse_unmatched_queries()

        return EvolutionReport(
            period_days=days,
            generated_at=date.today().isoformat(),
            overall=overall,
            intent_distribution=intent_stats,
            low_quality_items=low_quality,
            unmatched=unmatched,
        )

    async def _query_overall_metrics(self, days: int) -> OverallMetrics:
        since = date.today() - timedelta(days=days)
        result = await self._db.execute(text("""
            SELECT
                COUNT(*) AS total,
                COALESCE(AVG(duration_ms), 0) AS avg_duration,
                COALESCE(AVG(total_tokens), 0) AS avg_tokens,
                SUM(CASE WHEN user_feedback = -1 OR fallback_used = 1 OR steps_count >= 7 OR duration_ms > 30000 THEN 1 ELSE 0 END) AS low_quality_count,
                SUM(CASE WHEN user_feedback = 1 THEN 1 ELSE 0 END) AS positive_feedback
            FROM qa_session_log
            WHERE asked_at >= :since
        """), {"since": since})
        row = result.mappings().first()
        total = row["total"]
        low = row["low_quality_count"]
        pos = row["positive_feedback"]
        return OverallMetrics(
            total_qa=total,
            avg_duration_ms=float(row["avg_duration"]),
            avg_tokens=float(row["avg_tokens"]),
            low_quality_rate=low / total if total else 0,
            satisfaction_rate=pos / total if total else 0,
        )

    async def _query_intent_distribution(self, days: int) -> list[IntentStat]:
        since = date.today() - timedelta(days=days)
        result = await self._db.execute(text("""
            SELECT
                intent,
                COUNT(*) AS cnt,
                COALESCE(AVG(duration_ms), 0) AS avg_dur,
                SUM(CASE WHEN user_feedback = -1 OR fallback_used = 1 OR steps_count >= 7 OR duration_ms > 30000 THEN 1 ELSE 0 END) AS low_cnt
            FROM qa_session_log
            WHERE asked_at >= :since AND intent IS NOT NULL
            GROUP BY intent
            ORDER BY cnt DESC
        """), {"since": since})
        rows = result.mappings().all()
        total = sum(r["cnt"] for r in rows)
        return [
            IntentStat(
                intent=r["intent"],
                count=r["cnt"],
                pct=r["cnt"] / total if total else 0,
                low_quality_rate=r["low_cnt"] / r["cnt"] if r["cnt"] else 0,
                avg_duration_ms=float(r["avg_dur"]),
            )
            for r in rows
        ]

    async def _query_low_quality(self, days: int) -> list[dict]:
        since = date.today() - timedelta(days=days)
        result = await self._db.execute(text("""
            SELECT question, intent, user_feedback, fallback_used, steps_count, duration_ms, asked_at
            FROM qa_session_log
            WHERE asked_at >= :since
              AND (user_feedback = -1 OR fallback_used = 1 OR steps_count >= 7 OR duration_ms > 30000)
            ORDER BY asked_at DESC
        """), {"since": since})
        return [dict(r) for r in result.mappings()]

    def _parse_unmatched_queries(self) -> UnmatchedSummary:
        path = UNMATCHED_QUERIES_PATH
        if not path.exists():
            return UnmatchedSummary(total_new_this_week=0, total_accumulated=0, top_patterns=[])

        lines = path.read_text(encoding="utf-8").splitlines()
        total_accumulated = sum(1 for l in lines if l.startswith("| ") and "|" in l[2:])
        # Header is 3 lines (title + separator + header row), skip those
        data_lines = [l for l in lines if l.startswith("| ") and "|" in l[2:] and not l.startswith("| Time")]
        total_accumulated = len(data_lines)

        # New this week: lines with date within last 7 days
        week_ago = date.today() - timedelta(days=7)
        new_count = 0
        patterns: dict[str, int] = {}
        for line in data_lines:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                try:
                    line_date = date.fromisoformat(parts[0][:10])
                    if line_date >= week_ago:
                        new_count += 1
                except ValueError:
                    pass
                # Extract keywords from question for pattern detection
                question = parts[3] if len(parts) > 3 else ""
                keywords = self._extract_keywords(question)
                for kw in keywords:
                    patterns[kw] = patterns.get(kw, 0) + 1

        top = sorted(patterns.items(), key=lambda x: -x[1])[:5]
        return UnmatchedSummary(
            total_new_this_week=new_count,
            total_accumulated=total_accumulated,
            top_patterns=[f'"{k}" (appeared {v} times)' for k, v in top],
        )

    def _extract_keywords(self, question: str) -> list[str]:
        """Extract meaningful 2-char+ Chinese words as keyword patterns."""
        # Simple approach: look for common query patterns
        patterns = []
        for kw in ["完成", "考试", "学习", "通过", "成绩", "排名", "趋势", "建议", "风险", "规划"]:
            if kw in question:
                patterns.append(kw)
        return patterns if patterns else [question[:10]]
