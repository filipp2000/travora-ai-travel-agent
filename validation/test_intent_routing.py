from pydantic_models.travel_request import (
    RequestCheck,
    RequestIntent,
    TravelCapability,
    TravelRequest,
)
from workflow.nodes import scope_response_node
from workflow.routing import route_after_check, route_after_understanding


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
