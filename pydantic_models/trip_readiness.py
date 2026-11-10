
from enum import StrEnum

from pydantic import BaseModel, Field


class ReadinessIssue(StrEnum):
    """Reasons why the current trip context is not ready."""

    MISSING_CAPABILITY = "missing_capability"
    MISSING_DESTINATION = "missing_destination"
    MISSING_ORIGIN = "missing_origin"
    MISSING_DURATION = "missing_duration"

    MISSING_TRAVEL_PERIOD = "missing_travel_period"
    MISSING_TRAVEL_YEAR = "missing_travel_year"
    MISSING_START_DATE = "missing_start_date"
    MISSING_TRAVELERS = "missing_travelers"

    MISSING_BUDGET_CURRENCY = "missing_budget_currency"
    MISSING_BUDGET_SCOPE = "missing_budget_scope"

    INVALID_DATE_RANGE = "invalid_date_range"
    DURATION_DATE_MISMATCH = "duration_date_mismatch"
    PAST_START_DATE = "past_start_date"
    PAST_TRAVEL_MONTH = "past_travel_month"


class TripReadiness(BaseModel):
    """Result of deterministic trip completeness assessment."""

    ready: bool

    # Structured issue codes make the result testable and
    # independent of the wording of clarification questions.
    issues: list[ReadinessIssue] = Field(default_factory=list)
