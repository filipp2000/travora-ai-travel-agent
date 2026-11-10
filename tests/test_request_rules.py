# ---------------------------------------------------------
# Request Policy
# Tests for deterministic capability expansion.
# ---------------------------------------------------------
from pydantic_models.travel_request import (
    TravelCapability,
    TravelRequest,
)
from services.request_policy import (
    apply_request_policy,
)
from services.request_validation import check_request


def test_end_to_end_itinerary_adds_flights_and_hotels():
    request = TravelRequest(
        capabilities={
            TravelCapability.ITINERARY,
        },
        origin="my city",
        destination="Japan",
        duration_days=5,
        preferences=["budget"],
    )

    result = apply_request_policy(
        request
    )

    assert result.capabilities == {
        TravelCapability.FLIGHTS,
        TravelCapability.HOTELS,
        TravelCapability.ITINERARY,
    }


def test_destination_only_itinerary_does_not_add_flights():
    request = TravelRequest(
        capabilities={
            TravelCapability.ITINERARY,
        },
        destination="Japan",
        duration_days=5,
    )

    result = apply_request_policy(
        request
    )

    assert result.capabilities == {
        TravelCapability.ITINERARY,
    }


def test_hotel_only_request_is_not_modified():
    request = TravelRequest(
        capabilities={
            TravelCapability.HOTELS,
        },
        destination="Milan",
        budget_amount=120,
        budget_currency="USD",
    )

    result = apply_request_policy(
        request
    )

    assert result.capabilities == {
        TravelCapability.HOTELS,
    }


# ---------------------------------------------------------
# Request Validation
# Tests for execution readiness and airport resolution.
# ---------------------------------------------------------

def test_hotel_only_request_is_ready() -> None:
    request = TravelRequest(
        capabilities={TravelCapability.HOTELS},
        destination="Rome",
        budget_amount=120,
        budget_currency="EUR",
    )

    result = check_request(request)

    assert result.ready is True
    assert result.errors == []


def test_unresolved_origin_requires_clarification() -> None:
    request = TravelRequest(
        capabilities={
            TravelCapability.FLIGHTS,
            TravelCapability.HOTELS,
            TravelCapability.ITINERARY,
        },
        origin="my city",
        destination="Japan",
    )

    result = check_request(request)

    assert result.ready is False
    assert result.origin_iata is None
    assert result.destination_iata == "NRT"
    assert "unresolved_origin" in result.errors


def test_missing_origin_requires_clarification() -> None:
    request = TravelRequest(
        capabilities={TravelCapability.FLIGHTS},
        destination="Japan",
    )

    result = check_request(request)

    assert result.ready is False
    assert "missing_origin" in result.errors


def test_valid_flight_request_is_ready() -> None:
    request = TravelRequest(
        capabilities={TravelCapability.FLIGHTS},
        origin="Athens",
        destination="Tokyo",
    )

    result = check_request(request)

    assert result.ready is True
    assert result.origin_iata == "ATH"
    assert result.destination_iata == "NRT"
    assert result.errors == []