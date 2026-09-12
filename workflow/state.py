from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from pydantic_models.travel_request import (
    RequestCheck,
    TravelRequest,
)


class TravelState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]

    user_query: str

    parsed_request: TravelRequest | None
    request_check: RequestCheck | None

    flight_results: str
    hotel_results: str
    activity_results: str

    itinerary: str
    final_answer: str