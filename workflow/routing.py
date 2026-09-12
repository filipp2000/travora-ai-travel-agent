from pydantic_models.travel_request import TravelCapability
from workflow.state import TravelState


# Create the conditional routing logic for the workflow based on the state of the travel request.
def route_after_check(
    state: TravelState,
) -> str | list[str]:
    request_check = state["request_check"]
    parsed_request = state["parsed_request"]

    if request_check is None or parsed_request is None:
        raise ValueError(
            "Request must be parsed and checked before routing."
        )

    if not request_check.ready:
        return "clarify_request"

    capabilities = parsed_request.capabilities

    routes: list[str] = []

    if TravelCapability.FLIGHTS in capabilities:
        routes.append("flight_node")

    if TravelCapability.HOTELS in capabilities:
        routes.append("hotel_node")

    if TravelCapability.ACTIVITIES in capabilities:
        routes.append("activities_node")

    # Flights/hotels/activities can be retrieved first.
    if routes:
        return routes

    # An itinerary-only request needs no external retrieval.
    if TravelCapability.ITINERARY in capabilities:
        return "itinerary_node"

    return "final_response_node"


def route_after_research(
    state: TravelState,
) -> str:
    parsed_request = state["parsed_request"]

    if parsed_request is None:
        raise ValueError("Parsed request is missing.")

    if TravelCapability.ITINERARY in parsed_request.capabilities:
        return "itinerary_node"

    return "final_response_node"