from pydantic_models.travel_request import RequestIntent, TravelCapability
from pydantic_models.trip_readiness import TripReadiness
from workflow.state import TravelState


# Create the conditional routing logic for the workflow based on the state of the travel request.
def route_after_check(
    state: TravelState,
) -> str | list[str]:
    """
    Route a validated request to the external capabilities
    that require execution.
    """
    request_check = state["request_check"]
    parsed_request = state["parsed_request"]

    if request_check is None or parsed_request is None:
        raise ValueError("Request must be parsed and checked before routing.")

    # Reject requests without executable capabilities
    # before checking whether clarification is needed.
    if parsed_request.intent != RequestIntent.TRAVEL or not parsed_request.capabilities:
        return "scope_response"

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

    # External research is needed.
    if routes:
        return routes

    # No external research was requested.
    # Generate the requested answer directly.
    return "generate_response_node"


def route_after_research(
    state: TravelState,
) -> str:
    parsed_request = state["parsed_request"]

    if parsed_request is None:
        raise ValueError("Parsed request is missing.")

    if TravelCapability.ITINERARY in parsed_request.capabilities:
        return "itinerary_node"

    return "final_response_node"


def route_after_understanding(
    state: TravelState,
) -> str:
    """
    Decide whether to continue collecting trip information
    or reject a new out-of-scope request.
    """

    request = state.get("parsed_request")

    if request is None:
        raise ValueError("Parsed request is missing.")

    if request.intent != RequestIntent.TRAVEL:
        # During an existing clarification, unrelated messages
        # must not be merged or interpreted as destinations.
        # Reassess the unchanged context and ask again.
        if state.get("pending_question"):
            return "assess_trip_readiness"

        # Independent out-of-scope requests use the existing guardrail.
        return "scope_response"

    # Even requests with zero extracted capabilities reach readiness,
    # where missing_capability generates a targeted question.
    return "assess_trip_readiness"


def route_after_readiness(
    state: TravelState,
) -> str:
    """
    Continue to execution validation only when the
    accumulated trip context has passed readiness checks.
    """

    readiness = TripReadiness.model_validate(
        state["trip_readiness"]
    )

    if not readiness.ready:
        return "ask_trip_details"

    # Readiness does not automatically authorize research.
    return "present_trip_brief"


def route_after_brief_decision(
    state: TravelState,
) -> str:
    """
    Route only after the user has made an explicit
    decision at the trip brief confirmation gate.
    """

    decision = state.get("brief_decision")

    if decision == "edit":
        # Parse the user's corrections as another turn.
        return "understand_request"

    if decision == "build":
        # Only explicit approval reaches execution.
        return "check_request"

    raise ValueError(
        "Trip brief confirmation decision is missing."
    )