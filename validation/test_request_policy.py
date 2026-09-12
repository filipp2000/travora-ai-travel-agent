from pydantic_models.travel_request import (
    TravelCapability,
    TravelRequest,
)
from services.request_policy import (
    apply_request_policy,
)


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