from pydantic_models.travel_request import (
    RequestCheck,
    RequestIntent,
    TravelCapability,
    TravelRequest,
)
from workflow.nodes import scope_response_node
from workflow.routing import (
    route_after_check,
    route_after_understanding,
)

# ---------------------------------------------------------
# Intent routing
# Verify that unrelated or non-executable requests
# cannot reach the travel research workflow.
# ---------------------------------------------------------


def test_empty_capabilities_never_reach_generation():
    request = TravelRequest(
        intent=RequestIntent.TRAVEL,
        capabilities=set(),
        destination="What is Generative AI?",
    )

    state = {
        "parsed_request": request,
        "request_check": RequestCheck(
            ready=True,
        ),
    }

    assert route_after_check(state) == "scope_response"


def test_out_of_scope_request_is_not_validated():
    request = TravelRequest(
        intent=RequestIntent.OUT_OF_SCOPE,
        capabilities=set(),
    )

    state = {"parsed_request": request}

    assert route_after_understanding(state) == "scope_response"


def test_valid_hotel_request_reaches_validation():
    request = TravelRequest(
        intent=RequestIntent.TRAVEL,
        capabilities={TravelCapability.HOTELS},
        destination="Rome",
    )

    state = {"parsed_request": request}

    assert route_after_understanding(state) == "check_request"


def test_incomplete_flight_request_reaches_validation():
    request = TravelRequest(
        intent=RequestIntent.TRAVEL,
        capabilities={TravelCapability.FLIGHTS},
        origin="my city",
        destination="Tokyo",
    )

    state = {"parsed_request": request}

    assert route_after_understanding(state) == "check_request"


def test_unclear_request_does_not_call_research():
    request = TravelRequest(
        intent=RequestIntent.UNCLEAR,
        capabilities=set(),
    )

    state = {"parsed_request": request}

    assert route_after_understanding(state) == "scope_response"


def test_scope_response_requires_no_llm():
    request = TravelRequest(
        intent=RequestIntent.OUT_OF_SCOPE,
        capabilities=set(),
    )

    result = scope_response_node({"parsed_request": request})

    assert "travel planning" in result["final_answer"].lower()


# ---------------------------------------------------------
# Capability routing
# Verify which research nodes execute after validation.
# ---------------------------------------------------------


def test_complete_trip_routes_to_flights_and_hotels():
    state = {
        "parsed_request": TravelRequest(
            capabilities={
                TravelCapability.FLIGHTS,
                TravelCapability.HOTELS,
                TravelCapability.ITINERARY,
            },
            origin="Athens",
            destination="France",
            duration_days=5,
            budget_amount=2000,
            budget_currency="USD",
        ),
        "request_check": RequestCheck(
            ready=True,
            origin_iata="ATH",
            destination_iata="CDG",
        ),
    }

    result = route_after_check(state)

    assert result == [
        "flight_node",
        "hotel_node",
    ]


def test_complete_trip_with_activities_routes_to_all_research_nodes():
    state = {
        "parsed_request": TravelRequest(
            capabilities={
                TravelCapability.FLIGHTS,
                TravelCapability.HOTELS,
                TravelCapability.ITINERARY,
                TravelCapability.ACTIVITIES,
            },
            origin="Athens",
            destination="France",
        ),
        "request_check": RequestCheck(
            ready=True,
            origin_iata="ATH",
            destination_iata="CDG",
        ),
    }

    result = route_after_check(state)

    assert result == [
        "flight_node",
        "hotel_node",
        "activities_node",
    ]


def test_itinerary_only_routes_directly_to_generation():
    state = {
        "parsed_request": TravelRequest(
            capabilities={
                TravelCapability.ITINERARY,
            },
            destination="France",
            duration_days=5,
        ),
        "request_check": RequestCheck(
            ready=True,
        ),
    }

    result = route_after_check(state)

    assert result == "generate_response_node"


def test_hotel_only_routes_only_to_hotel_research():
    state = {
        "parsed_request": TravelRequest(
            capabilities={
                TravelCapability.HOTELS,
            },
            destination="Paris",
        ),
        "request_check": RequestCheck(
            ready=True,
        ),
    }

    result = route_after_check(state)

    assert result == [
        "hotel_node",
    ]


def test_invalid_request_routes_to_clarification():
    state = {
        "parsed_request": TravelRequest(
            capabilities={
                TravelCapability.FLIGHTS,
            },
            origin="my city",
            destination="Japan",
        ),
        "request_check": RequestCheck(
            ready=False,
            destination_iata="NRT",
            errors=["unresolved_origin"],
        ),
    }

    result = route_after_check(state)

    assert result == "clarify_request"
