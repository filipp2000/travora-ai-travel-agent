
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from pydantic_models.travel_request import TravelCapability


class BudgetScope(StrEnum):
    TOTAL_TRIP = "total_trip"
    PER_NIGHT = "per_night"


class TripContext(BaseModel):
    """Accumulated travel information across user turns."""

    capabilities: set[TravelCapability] = Field(default_factory=set)

    origin: str | None = None
    destination: str | None = None

    duration_days: int | None = Field(default=None, ge=1, le=60)

    start_date: date | None = None
    end_date: date | None = None

    # YYYY-MM, e.g. "2026-12"
    travel_month: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )

    dates_flexible: bool = False

    travelers: int | None = Field(default=None, ge=1, le=30)

    budget_amount: float | None = Field(default=None, gt=0)
    budget_currency: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{3}$",
    )
    budget_scope: BudgetScope | None = None

    preferences: list[str] = Field(default_factory=list)


class TripContextUpdate(BaseModel):
    """Fields extracted or explicitly corrected in one user turn."""

    origin: str | None = None
    destination: str | None = None

    duration_days: int | None = None

    start_date: date | None = None
    end_date: date | None = None
    travel_month: str | None = None
    dates_flexible: bool | None = None

    travelers: int | None = None

    budget_amount: float | None = None
    budget_currency: str | None = None
    budget_scope: BudgetScope | None = None

    add_preferences: list[str] = Field(default_factory=list)
    remove_preferences: list[str] = Field(default_factory=list)
