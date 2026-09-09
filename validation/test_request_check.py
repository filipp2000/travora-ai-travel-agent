from pydantic_models.travel_request import (
    TravelCapability,
    TravelRequest,
)

from validation.request_check import check_request

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