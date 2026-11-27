from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from pydantic_models.api_response import ResponseType
from pydantic_models.travel_request import (
    RequestCheck,
    TravelRequest,
)
from pydantic_models.trip_context import TripContext
from pydantic_models.trip_readiness import TripReadiness


class TravelState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    # Persistent marker used by the API to reject planning session
    session_cancelled: bool

    # Accumulated planning data for the current trip.
    trip_context: TripContext | None
    # Deterministic completeness assessment of that context.
    trip_readiness: TripReadiness | None

    # Last question asked during the collection phase.
    # Helps interpret user replies
    pending_question: str | None

    latest_user_message: str
    turn_source: Literal["trip_details", "trip_brief"]
    repeat_pending_phase: bool

    # Most recent accepted planning input, also used by synthesis.
    user_query: str

    parsed_request: TravelRequest | None
    request_check: RequestCheck | None

    flight_results: str
    hotel_results: str
    activity_results: str

    itinerary: str
    
    # The most recent decision from the trip brief interrupt.
    # Used only to route after the user resumes the workflow.
    brief_decision: str | None
    
    final_answer: str
    terminal_response_type: ResponseType
