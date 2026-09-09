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
    capabilities: set[TravelCapability]

    origin: str | None = None
    destination: str | None = None

    duration_days: int | None = None

    budget_amount: float | None = None
    budget_currency: str | None = None

    travelers: int | None = None
    preferences: list[str] = Field(default_factory=list)


# Whether app has enough usable information to execute the request.
class RequestCheck(BaseModel):
    ready: bool

    origin_iata: str | None = None
    destination_iata: str | None = None

    errors: list[str] = Field(default_factory=list)