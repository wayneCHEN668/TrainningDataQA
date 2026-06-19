"""Pydantic input models for all 16 tools (13 registered + 3 pure-LLM)."""
from pydantic import BaseModel, Field


# -- Q1: query_completion_rate --
class CompletionRateInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class/individual")
    time_start: str = Field(description="YYYY-MM-DD")
    time_end: str = Field(description="YYYY-MM-DD")
    course_code: str | None = Field(default=None)
    group_by: str = Field(default="none", description="none/dept/class/course")


# -- Q2: query_incomplete_learners --
class IncompleteLearnersInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class")
    course_code: str = Field(description="Course code to check")
    urgency_threshold_days: int = Field(default=7, description="Days before deadline to mark as urgent")


# -- Q3: query_exam_performance --
class ExamPerformanceInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class")
    exam_session_code: str | None = Field(default=None)
    time_start: str | None = Field(default=None)
    time_end: str | None = Field(default=None)
    group_by: str = Field(default="none", description="none/dept/exam")


# -- Q4: query_skill_error_analysis --
class SkillErrorInput(BaseModel):
    courseware_code: str = Field(description="Courseware code to analyze")
    top_n: int = Field(default=10, ge=1, le=50)


# -- Q5: query_learning_trend --
class LearningTrendInput(BaseModel):
    scope_type: str = Field(description="all/org/dept")
    metric: str = Field(description="study_minutes/completions/exam_pass/active_users")
    time_start: str = Field(description="YYYY-MM-DD")
    time_end: str = Field(description="YYYY-MM-DD")
    granularity: str = Field(default="week", description="day/week/month")


# -- Q6: query_at_risk_learners --
class AtRiskLearnersInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class")
    risk_types: list[str] = Field(default=["inactive", "low_score", "near_deadline"])


# -- Q7: query_individual_profile --
class IndividualProfileInput(BaseModel):
    user_code: str = Field(description="Student/staff code to look up")


# -- Q8: query_org_overview --
class OrgOverviewInput(BaseModel):
    time_start: str = Field(description="YYYY-MM-DD")
    time_end: str = Field(description="YYYY-MM-DD")


# -- C1: compute_period_comparison --
class PeriodComparisonInput(BaseModel):
    data_current: list[dict] = Field(description="Current period data points")
    data_previous: list[dict] = Field(description="Previous period data points")
    key_field: str = Field(description="Field name to compare (e.g., completion_rate)")


# -- C2: detect_anomalies --
class AnomalyDetectionInput(BaseModel):
    data_points: list[dict] = Field(description="Time series: [{date, value}]")
    threshold_sigma: float = Field(default=2.0, ge=0.5, le=5.0)


# -- C3: evaluate_metric_level --
class MetricLevelInput(BaseModel):
    metric_value: float = Field(description="The metric value to evaluate")
    benchmark_value: float = Field(description="Average benchmark for comparison")
    percentile_bands: dict | None = Field(default=None, description="{p25, p50, p75}")


# -- A1: get_benchmark --
class BenchmarkInput(BaseModel):
    scope_type: str = Field(description="dept/org")
    scope_code: str = Field(description="Dept or org code")
    stat_period: str = Field(default="month", description="month/quarter/year")


# -- A2: search_course_or_exam --
class SearchCourseExamInput(BaseModel):
    query: str = Field(description="Fuzzy course or exam name to search")
    search_type: str = Field(default="all", description="course/exam/all")


# -- V1: generate_chart_spec (Pure-LLM tool) --
class ChartSpecInput(BaseModel):
    chart_type: str = Field(description="bar/line/pie")
    title: str = Field(description="Chart title in Chinese")
    data: list[dict] = Field(description="Data points for the chart, e.g. [{name, value}] or [{date, value}]")
    x_key: str = Field(default="name", description="Key for x-axis / category")
    y_key: str = Field(default="value", description="Key for y-axis / value")
    color: str = Field(default="#4f8ef7", description="Primary color hex code")


# -- New tools added for Phase 7 (fixing test gaps) --

class RoleDistributionInput(BaseModel):
    """Count users by role_level with optional dept grouping."""
    group_by: str = Field(default="role", description="role/dept/both")


class ClassStudentsInput(BaseModel):
    """List students in a specific class."""
    class_code: str = Field(description="Class code, e.g. 'class2026'")
    include_profile: bool = Field(default=False, description="Include extended profile details")


class DeptClassesInput(BaseModel):
    """List classes under a department with student counts."""
    dept_code: str = Field(description="Department code, e.g. 'DEPT01'")


class EntityCountInput(BaseModel):
    """Count entities in a given table."""
    entity_type: str = Field(description="Entity type: course/exam/user/class/dept/org")
    scope_type: str = Field(default="all", description="Scope filter: all/org/dept")
