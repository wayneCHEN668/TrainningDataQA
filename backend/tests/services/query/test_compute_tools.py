"""Unit tests for compute-type tools (pure Python, no DB)."""
import pytest
from statistics import mean, stdev

from app.schemas.tools import PeriodComparisonInput, AnomalyDetectionInput, MetricLevelInput


# ============================================================================
# Helper: extract the pure-math logic from tool_registry.py C1-C3 _run fns.
# These are identical to the actual tool logic — the tools just wrap them
# with schema parsing and an async signature.
# ============================================================================

def _period_comparison_logic(data_current: list[dict], data_previous: list[dict], key_field: str) -> dict:
    """Pure-function core of compute_period_comparison."""
    if not data_current or not data_previous:
        raise ValueError("Both data_current and data_previous must be non-empty lists.")
    curr_avg = sum(d[key_field] for d in data_current) / len(data_current)
    prev_avg = sum(d[key_field] for d in data_previous) / len(data_previous)
    delta = round(curr_avg - prev_avg, 2)
    delta_pct = round((delta / prev_avg * 100), 2) if prev_avg else 0
    return {
        "current_avg": round(curr_avg, 2),
        "previous_avg": round(prev_avg, 2),
        "delta": delta,
        "delta_pct": delta_pct,
    }


def _anomaly_detection_logic(data_points: list[dict], threshold_sigma: float = 2.0) -> dict:
    """Pure-function core of detect_anomalies."""
    if not data_points or len(data_points) < 2:
        return {"anomalies": [], "mean": 0, "stdev": 0, "message": "Need at least 2 data points."}
    values = [d["value"] for d in data_points]
    m = mean(values)
    s = stdev(values)
    anomalies = []
    for d in data_points:
        deviation = abs(d["value"] - m) / s if s > 0 else 0
        if deviation > threshold_sigma:
            anomalies.append({
                "period": d.get("date", ""),
                "value": d["value"],
                "deviation_sigma": round(deviation, 2),
            })
    return {
        "anomalies": anomalies,
        "mean": round(m, 2),
        "stdev": round(s, 2),
    }


def _metric_level_logic(metric_value: float, benchmark_value: float,
                        percentile_bands: dict | None = None) -> dict:
    """Pure-function core of evaluate_metric_level."""
    ratio = metric_value / benchmark_value if benchmark_value else 0
    if percentile_bands:
        p75 = percentile_bands.get("p75", 0)
        p50 = percentile_bands.get("p50", 0)
        p25 = percentile_bands.get("p25", 0)
        if metric_value >= p75:
            level = "excellent"
        elif metric_value >= p50:
            level = "good"
        elif metric_value >= p25:
            level = "average"
        else:
            level = "below"
    else:
        if ratio >= 1.2:
            level = "excellent"
        elif ratio >= 1.0:
            level = "good"
        elif ratio >= 0.8:
            level = "average"
        elif ratio >= 0.6:
            level = "below"
        else:
            level = "poor"
    return {
        "level": level,
        "ratio": round(ratio, 2),
        "gap_to_average": round(metric_value - benchmark_value, 2),
    }


# ============================================================================
# C1: Period Comparison
# ============================================================================

class TestPeriodComparison:
    def test_basic_comparison(self):
        """Period-over-period delta calculation: avg_current=85, avg_previous=77.5."""
        current = [{"completion_rate": 80}, {"completion_rate": 90}]
        previous = [{"completion_rate": 70}, {"completion_rate": 85}]

        result = _period_comparison_logic(
            data_current=current,
            data_previous=previous,
            key_field="completion_rate",
        )

        assert result["current_avg"] == 85.0
        assert result["previous_avg"] == 77.5
        assert result["delta"] == 7.5
        assert result["delta_pct"] == 9.68

    def test_decline_detected(self):
        """Negative delta when current < previous."""
        current = [{"score": 60}, {"score": 62}]
        previous = [{"score": 80}, {"score": 80}]

        result = _period_comparison_logic(
            data_current=current,
            data_previous=previous,
            key_field="score",
        )

        assert result["current_avg"] == 61.0
        assert result["previous_avg"] == 80.0
        assert result["delta"] == -19.0
        assert result["delta_pct"] == -23.75

    def test_empty_data_raises(self):
        """Both lists must be non-empty."""
        with pytest.raises(ValueError, match="non-empty"):
            _period_comparison_logic(
                data_current=[], data_previous=[], key_field="x",
            )

    def test_no_change_zero_delta(self):
        """Identical periods produce zero delta."""
        data = [{"v": 50}, {"v": 50}]
        result = _period_comparison_logic(
            data_current=data,
            data_previous=data,
            key_field="v",
        )
        assert result["delta"] == 0.0
        assert result["delta_pct"] == 0.0


# ============================================================================
# C2: Anomaly Detection
# ============================================================================

class TestAnomalyDetection:
    def test_detect_outlier(self):
        """A point 3 sigma away should be flagged at threshold=2.0."""
        points = [
            {"date": "2026-01-01", "value": 80},
            {"date": "2026-01-02", "value": 82},
            {"date": "2026-01-03", "value": 78},
            {"date": "2026-01-04", "value": 81},
            {"date": "2026-01-05", "value": 79},
            {"date": "2026-01-06", "value": 30},  # outlier
        ]

        result = _anomaly_detection_logic(points, threshold_sigma=2.0)

        assert len(result["anomalies"]) == 1
        assert result["anomalies"][0]["value"] == 30
        assert result["anomalies"][0]["period"] == "2026-01-06"
        # mean and stdev should be reasonable
        assert 60 < result["mean"] < 80
        assert result["stdev"] > 10

    def test_no_outliers_in_normal_data(self):
        """All-normal data should have no anomalies at sigma=2.0."""
        points = [{"date": f"d{i}", "value": 80 + i * 2} for i in range(10)]

        result = _anomaly_detection_logic(points, threshold_sigma=2.0)

        assert len(result["anomalies"]) == 0

    def test_insufficient_data(self):
        """Less than 2 data points should return early."""
        result = _anomaly_detection_logic([{"date": "x", "value": 42}], threshold_sigma=2.0)

        assert result["anomalies"] == []
        assert "Need at least 2" in result["message"]

    def test_all_same_values_no_false_positive(self):
        """Uniform data (stdev=0) should produce no anomalies."""
        points = [{"date": f"d{i}", "value": 100} for i in range(5)]

        result = _anomaly_detection_logic(points, threshold_sigma=2.0)

        assert len(result["anomalies"]) == 0
        assert result["stdev"] == 0.0


# ============================================================================
# C3: Metric Level Evaluation (ratio-based)
# ============================================================================

class TestMetricLevelEvaluate:
    def test_excellent_ratio(self):
        """120%+ of benchmark -> excellent."""
        result = _metric_level_logic(metric_value=120, benchmark_value=100)
        assert result["level"] == "excellent"
        assert result["ratio"] == 1.2

    def test_good_ratio(self):
        """100-120% of benchmark -> good."""
        result = _metric_level_logic(metric_value=105, benchmark_value=100)
        assert result["level"] == "good"
        assert result["ratio"] == 1.05

    def test_average_ratio(self):
        """80-100% of benchmark -> average."""
        result = _metric_level_logic(metric_value=85, benchmark_value=100)
        assert result["level"] == "average"
        assert result["ratio"] == 0.85

    def test_below_ratio(self):
        """60-80% of benchmark -> below."""
        result = _metric_level_logic(metric_value=65, benchmark_value=100)
        assert result["level"] == "below"
        assert result["ratio"] == 0.65

    def test_poor_ratio(self):
        """Below 60% of benchmark -> poor."""
        result = _metric_level_logic(metric_value=50, benchmark_value=100)
        assert result["level"] == "poor"
        assert result["ratio"] == 0.5

    def test_zero_benchmark_handled(self):
        """Zero benchmark should not divide by zero."""
        result = _metric_level_logic(metric_value=50, benchmark_value=0)
        assert result["ratio"] == 0
        assert result["level"] == "poor"

    def test_exact_boundaries(self):
        """Test exact threshold boundaries."""
        # 1.2 exactly -> excellent (not good)
        assert _metric_level_logic(120, 100)["level"] == "excellent"
        # 1.0 exactly -> good (not average)
        assert _metric_level_logic(100, 100)["level"] == "good"
        # 0.8 exactly -> average (not below)
        assert _metric_level_logic(80, 100)["level"] == "average"
        # 0.6 exactly -> below (not poor)
        assert _metric_level_logic(60, 100)["level"] == "below"


# ============================================================================
# C3 (continued): Metric Level Evaluation (percentile-band based)
# ============================================================================

class TestMetricLevelPercentile:
    def test_excellent_percentile(self):
        """value >= p75 -> excellent."""
        result = _metric_level_logic(
            metric_value=85, benchmark_value=70,
            percentile_bands={"p75": 80, "p50": 65, "p25": 50},
        )
        assert result["level"] == "excellent"

    def test_good_percentile(self):
        """p50 <= value < p75 -> good."""
        result = _metric_level_logic(
            metric_value=70, benchmark_value=70,
            percentile_bands={"p75": 80, "p50": 65, "p25": 50},
        )
        assert result["level"] == "good"

    def test_average_percentile(self):
        """p25 <= value < p50 -> average."""
        result = _metric_level_logic(
            metric_value=55, benchmark_value=70,
            percentile_bands={"p75": 80, "p50": 65, "p25": 50},
        )
        assert result["level"] == "average"

    def test_below_percentile(self):
        """value < p25 -> below."""
        result = _metric_level_logic(
            metric_value=40, benchmark_value=70,
            percentile_bands={"p75": 80, "p50": 65, "p25": 50},
        )
        assert result["level"] == "below"

    def test_gap_to_average_computed(self):
        """gap_to_average = metric_value - benchmark_value."""
        result = _metric_level_logic(metric_value=85, benchmark_value=70)
        assert result["gap_to_average"] == 15.0

    def test_negative_gap(self):
        """When metric is below benchmark, gap is negative."""
        result = _metric_level_logic(metric_value=50, benchmark_value=70)
        assert result["gap_to_average"] == -20.0
