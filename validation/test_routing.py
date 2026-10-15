from pydantic_models.travel_request import (
    RequestCheck,
    TravelCapability,
    TravelRequest,
)
from workflow.routing import route_after_check


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
