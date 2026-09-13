from enum import StrEnum
from pydantic import BaseModel, Field

# Create a travel request domain model
class TravelCapability(StrEnum):
    FLIGHTS = "flights"
    HOTELS = "hotels"
    ITINERARY = "itinerary"
    ACTIVITIES = "activities"


# What the parsed user request
class TravelRequest(BaseModel):
    capabilities: set[TravelCapability] = Field(
        description=(
            "Travel capabilities explicitly or clearly requested by the user."
        )
    )

    origin: str | None = Field(
        default=None,
        description=(
            "Departure city, country, airport, or phrase supplied by the user. "
            "Do not infer the user's location."
        ),
    )
    destination: str | None = Field(
        default=None,
        description=(
            "Destination city, country, airport, or phrase supplied by the user. "
        ),
    )

    duration_days: int | None = Field(
        default=None,
        description=(
            "Duration of the trip in days."
        ),
    )

    budget_amount: float | None = Field(
        default=None,
        description=(
            "Maximum amount the user is willing to spend on the trip."
        ),
    )
    budget_currency: str | None = Field(
        default=None,
        description=(
            "Currency code such as USD or EUR when a budget is provided."
        ),
    )

    travelers: int | None = Field(
        default=None,
        description="Number of travelers, if explicitly provided.",
    )
    
    preferences: list[str] = Field(
        default_factory=list,
        description=(
            "Relevant travel preferences such as budget, luxury, family, "
            "nightlife, beaches, museums, or vegetarian."
        ),
    )


# Whether app has enough usable information to execute the request.
class RequestCheck(BaseModel):
    ready: bool

    origin_iata: str | None = None
    destination_iata: str | None = None

    errors: list[str] = Field(default_factory=list)