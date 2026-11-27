from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, model_validator

from pydantic_models.api_request import ThreadId


class ResponseType(StrEnum):
    MESSAGE = "message"
    CLARIFICATION = "clarification"
    TRIP_BRIEF = "trip_brief"
    TRAVEL_RESULT = "travel_result"


class SessionStatus(StrEnum):
    REQUIRES_INPUT = "requires_input"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


RESPONSE_TYPES_BY_STATUS = {
    SessionStatus.REQUIRES_INPUT: {ResponseType.CLARIFICATION},
    SessionStatus.REQUIRES_CONFIRMATION: {ResponseType.TRIP_BRIEF},
    SessionStatus.COMPLETED: {ResponseType.MESSAGE, ResponseType.TRAVEL_RESULT},
    SessionStatus.CANCELLED: {ResponseType.MESSAGE},
}


class TravelResponse(BaseModel):
    success: Literal[True] = True
    status: SessionStatus
    response_type: ResponseType
    thread_id: ThreadId
    answer: str
    flight_results: str = ""
    hotel_results: str = ""
    activity_results: str = ""
    itinerary: str = ""
    brief: dict[str, object] | None = None

    @model_validator(mode="after")
    def validate_response_contract(self) -> Self:
        if self.response_type not in RESPONSE_TYPES_BY_STATUS[self.status]:
            raise ValueError("Response type does not match the session status.")

        if self.response_type == ResponseType.TRIP_BRIEF:
            if not self.brief:
                raise ValueError("A trip brief response requires a structured brief.")
        elif self.brief is not None:
            raise ValueError("Only a trip brief response can include a brief.")

        return self
