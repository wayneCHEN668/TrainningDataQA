"""Unit tests for EvolutionAnalyzer."""
import json
import pytest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai.evolution_analyzer import (
    EvolutionAnalyzer,
    EvolutionReport,
    OverallMetrics,
    IntentStat,
    UnmatchedSummary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_metrics():
    return OverallMetrics(
        total_qa=100,
        avg_duration_ms=5000.0,
        avg_tokens=3000.0,
        low_quality_rate=0.1,
        satisfaction_rate=0.85,
    )


@pytest.fixture
def sample_report(sample_metrics):
    return EvolutionReport(
        period_days=7,
        generated_at="2026-06-19",
        overall=sample_metrics,
        intent_distribution=[
            IntentStat(
                intent="COMPLETION_RATE_QUERY",
                count=50,
                pct=0.5,
                low_quality_rate=0.05,
                avg_duration_ms=3000,
            ),
            IntentStat(
                intent="EXAM_QUERY",
                count=30,
                pct=0.3,
                low_quality_rate=0.25,
                avg_duration_ms=7000,
            ),
        ],
        low_quality_items=[],
        unmatched=UnmatchedSummary(
            total_new_this_week=5,
            total_accumulated=20,
            top_patterns=['"完成率" (3 times)'],
        ),
    )


# ---------------------------------------------------------------------------
# Test: Unmatched query parsing
# ---------------------------------------------------------------------------

class TestUnmatchedParsing:
    def test_empty_file_returns_zeros(self, mock_db):
        analyzer = EvolutionAnalyzer(mock_db)
        with patch.object(Path, "exists", return_value=False):
            result = analyzer._parse_unmatched_queries()
            assert result.total_new_this_week == 0
            assert result.total_accumulated == 0
            assert result.top_patterns == []

    def test_parses_markdown_table(self, mock_db):
        content = (
            "# Unmatched Queries\n\n"
            "| Time | User | Role | Question |\n"
            "|------|------|------|----------|\n"
            "| 2026-06-15 14:30 | Test | admin | 完成率怎么样 |\n"
        )
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value=content):
                analyzer = EvolutionAnalyzer(mock_db)
                result = analyzer._parse_unmatched_queries()
                assert result.total_accumulated == 1

    def test_handles_malformed_lines(self, mock_db):
        content = (
            "# Unmatched\n\n"
            "| Time | User | Role | Question |\n"
            "|------|------|------|----------|\n"
            "| bad line |\n"
            "| 2026-06-15 14:30 | Test | admin | 正常 |\n"
        )
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value=content):
                analyzer = EvolutionAnalyzer(mock_db)
                result = analyzer._parse_unmatched_queries()
                # At least the valid row should be counted
                assert result.total_accumulated >= 1

    def test_new_this_week_filters_by_date(self, mock_db):
        """Rows within the last 7 days should be counted as new_this_week."""
        today = date.today()
        recent = today.isoformat()
        old = (today - timedelta(days=10)).isoformat()
        content = (
            "# Unmatched\n\n"
            "| Time | User | Role | Question |\n"
            "|------|------|------|----------|\n"
            f"| {recent} 14:30 | Test | admin | 完成率怎么样 |\n"
            f"| {old} 10:00 | Old | user | 旧数据 |\n"
        )
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value=content):
                analyzer = EvolutionAnalyzer(mock_db)
                result = analyzer._parse_unmatched_queries()
                assert result.total_new_this_week == 1
                assert result.total_accumulated == 2


# ---------------------------------------------------------------------------
# Test: Keyword extraction (instance method on EvolutionAnalyzer)
# ---------------------------------------------------------------------------

class TestKeywordExtraction:
    def test_extracts_chinese_keywords(self, mock_db):
        analyzer = EvolutionAnalyzer(mock_db)
        result = analyzer._extract_keywords("考试通过率怎么样")
        assert "考试" in result

    def test_extracts_multiple_keywords(self, mock_db):
        analyzer = EvolutionAnalyzer(mock_db)
        result = analyzer._extract_keywords("完成率和考试成绩")
        assert "完成" in result
        assert "考试" in result
        assert "成绩" in result

    def test_returns_substring_when_no_match(self, mock_db):
        analyzer = EvolutionAnalyzer(mock_db)
        result = analyzer._extract_keywords("xyz123")
        assert len(result) > 0
        assert result == ["xyz123"]

    def test_empty_question_returns_prefix(self, mock_db):
        analyzer = EvolutionAnalyzer(mock_db)
        result = analyzer._extract_keywords("")
        assert result == [""]


# ---------------------------------------------------------------------------
# Test: Report formatting
# ---------------------------------------------------------------------------

class TestReportFormatting:
    def test_to_markdown_has_all_sections(self, sample_report):
        md = sample_report.to_markdown()
        assert "S1 Overall Metrics" in md
        assert "S2 Intent Distribution" in md
        assert "S3 Unmatched Queries" in md
        assert "S4 Improvement Suggestions" in md

    def test_to_markdown_includes_high_low_quality_flag(self, sample_report):
        md = sample_report.to_markdown()
        # The second intent has low_quality_rate 0.25, which is >0.2
        assert "HIGH" in md

    def test_to_summary_json_is_valid(self, sample_report):
        js = sample_report.to_summary_json()
        data = json.loads(js)
        assert data["overall"]["total_qa"] == 100
        assert data["overall"]["avg_duration_ms"] == 5000.0
        assert data["overall"]["low_quality_rate"] == 0.1
        assert len(data["top_intents"]) > 0
        assert data["top_intents"][0]["intent"] == "COMPLETION_RATE_QUERY"

    def test_to_summary_json_includes_unmatched(self, sample_report):
        js = sample_report.to_summary_json()
        data = json.loads(js)
        assert data["unmatched_new"] == 5
        assert data["unmatched_total"] == 20


# ---------------------------------------------------------------------------
# Test: Low-quality detection rules (the SQL WHERE clause constants)
# ---------------------------------------------------------------------------

class TestLowQualityRules:
    """Verify the low-quality detection constants are correct."""

    def test_negative_feedback_rule(self):
        from app.services.ai.evolution_analyzer import LOW_QUALITY_RULES
        assert LOW_QUALITY_RULES["negative_feedback"] == "user_feedback = -1"

    def test_fallback_used_rule(self):
        from app.services.ai.evolution_analyzer import LOW_QUALITY_RULES
        assert LOW_QUALITY_RULES["fallback_used"] == "fallback_used = 1"

    def test_too_many_steps_rule(self):
        from app.services.ai.evolution_analyzer import LOW_QUALITY_RULES
        assert LOW_QUALITY_RULES["too_many_steps"] == "steps_count >= 7"

    def test_too_slow_rule(self):
        from app.services.ai.evolution_analyzer import LOW_QUALITY_RULES
        assert LOW_QUALITY_RULES["too_slow"] == "duration_ms > 30000"


# ---------------------------------------------------------------------------
# Test: OverallMetrics dataclass
# ---------------------------------------------------------------------------

class TestOverallMetrics:
    def test_default_values(self):
        m = OverallMetrics()
        assert m.total_qa == 0
        assert m.avg_duration_ms == 0
        assert m.avg_tokens == 0
        assert m.low_quality_rate == 0
        assert m.satisfaction_rate == 0
        assert m.daily_trend == []

    def test_partial_initialization(self):
        m = OverallMetrics(total_qa=50, low_quality_rate=0.2)
        assert m.total_qa == 50
        assert m.low_quality_rate == 0.2
        assert m.avg_duration_ms == 0  # default


# ---------------------------------------------------------------------------
# Test: IntentStat dataclass
# ---------------------------------------------------------------------------

class TestIntentStat:
    def test_creation(self):
        s = IntentStat(intent="TEST", count=10, pct=0.25, low_quality_rate=0.05, avg_duration_ms=1200)
        assert s.intent == "TEST"
        assert s.count == 10
        assert s.pct == 0.25
        assert s.low_quality_rate == 0.05
        assert s.avg_duration_ms == 1200


# ---------------------------------------------------------------------------
# Test: UnmatchedSummary dataclass
# ---------------------------------------------------------------------------

class TestUnmatchedSummary:
    def test_creation(self):
        u = UnmatchedSummary(total_new_this_week=3, total_accumulated=15, top_patterns=["完成率"])
        assert u.total_new_this_week == 3
        assert u.total_accumulated == 15
        assert u.top_patterns == ["完成率"]
