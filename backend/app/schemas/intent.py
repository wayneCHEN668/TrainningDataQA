"""Intent classification data models."""
from pydantic import BaseModel, Field, field_validator


class SlotValues(BaseModel):
    """Query slots extracted from user question."""
    time_range: dict | None = Field(
        default_factory=lambda: {"type": "this_month"},
        description="Time range: {type: today/this_week/this_month/last_month/custom, start: YYYY-MM-DD, end: YYYY-MM-DD}"
    )

    @field_validator("time_range", mode="before")
    @classmethod
    def _normalize_time_range(cls, v: str | dict | None) -> dict | None:
        """Accept both string shorthand ("last_week") and object ({"type": "last_week"})."""
        if v is None:
            return {"type": "this_month"}
        if isinstance(v, str):
            # LLM may output a plain string despite JSON schema declaring object
            valid_types = {"today", "this_week", "this_month", "last_month",
                           "this_quarter", "this_year", "custom"}
            if v.strip() in valid_types:
                return {"type": v.strip()}
            # Unknown string → treat as custom with no date range
            return {"type": "custom"}
        if isinstance(v, dict) and "type" not in v:
            return {"type": "this_month"}
        return v
    scope_type: str = Field(
        default="all",
        description="Scope: all/org/dept/class/individual"
    )
    scope_name: str | None = Field(default=None)
    course_name: str | None = Field(default=None)
    exam_name: str | None = Field(default=None)
    metric: str | None = Field(default=None)
    compare_with_previous: bool = Field(default=False)
    top_n: int = Field(default=10, ge=1, le=100)
    granularity: str = Field(default="week", description="day/week/month")


class IntentResult(BaseModel):
    """Full intent classification result."""
    intent: str = Field(description="One of 22 intent codes")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    complexity: str = Field(default="simple", description="simple/moderate/complex")
    slots: SlotValues = Field(default_factory=SlotValues)
    need_clarification: bool = Field(default=False)
    clarification_question: str | None = Field(default=None)
    output_mode: str = Field(default="analysis", description="analysis | report")


class ClarificationOption(BaseModel):
    """Rephrased question option for user selection."""
    index: int = Field(ge=1, le=3)
    text: str
    intent: str
