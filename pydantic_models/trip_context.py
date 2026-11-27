from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from pydantic_models.travel_request import RequestIntent, TravelCapability

# Accept both YYYY-MM and MM.
# Examples: "2026-12" or "12" when the year is unspecified.
TRAVEL_MONTH_PATTERN = r"^(?:\d{4}-(?:0[1-9]|1[0-2])|(?:0[1-9]|1[0-2]))$"


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
        pattern=TRAVEL_MONTH_PATTERN,
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
    """Fields extracted or explicitly corrected from the latest user message."""

    capabilities: set[TravelCapability] | None = Field(
        default=None,
        description=(
            "New travel capabilities requested in the latest turn. "
            "Do not repeat capabilities already in the trip context."
        ),
    )

    origin: str | None = None
    destination: str | None = None

    duration_days: int | None = None

    start_date: date | None = None
    end_date: date | None = None
    travel_month: str | None = Field(
        default=None,
        pattern=TRAVEL_MONTH_PATTERN,
    )
    dates_flexible: bool | None = None

    travelers: int | None = None

    budget_amount: float | None = None
    budget_currency: str | None = None
    budget_scope: BudgetScope | None = None

    add_preferences: list[str] = Field(default_factory=list)
    remove_preferences: list[str] = Field(default_factory=list)
    
    @field_validator(
    "add_preferences",
    "remove_preferences",
    mode="before",
)
    @classmethod
    def normalize_preference_lists(cls, value):
        """
        Normalize null preference operations from LLM output.

        An omitted or null preference operation means no change.
        Other values still go through normal Pydantic validation.
        """

        # Structured LLM outputs may explicitly return null
        # instead of an empty array when no preferences are given.
        if value is None:
            return []

        # Preserve actual lists and let Pydantic validate their items.
        return value


class TripTurn(BaseModel):
    """Structured interpretation of one conversational user turn."""

    intent: RequestIntent = Field(
        description=(
            "Whether the latest message is travel-related, a standalone "
            "greeting, out of scope, or unclear in the current context."
        ),
    )

    update: TripContextUpdate = Field(
        description=(
            "Only the new or explicitly corrected trip information "
            "provided in the latest message."
        ),
    )
