from pydantic_models.travel_request import (
    RequestCheck,
    TravelCapability,
    TravelRequest,
)
from services.location_resolver import resolve_location_to_iata


def check_request(request: TravelRequest) -> RequestCheck:
    errors: list[str] = []

    origin_iata = None
    destination_iata = None

    # Every supported travel request currently needs a destination.
    if not request.destination:
        errors.append("missing_destination")

    # Airport resolution only matters when flights are requested.
    if TravelCapability.FLIGHTS in request.capabilities:

        if not request.origin:
            errors.append("missing_origin")
        else:
            origin_iata = resolve_location_to_iata(request.origin)

            if not origin_iata:
                errors.append("unresolved_origin")

        if request.destination:
            destination_iata = resolve_location_to_iata(
                request.destination
            )

            if not destination_iata:
                errors.append("unresolved_destination")

    return RequestCheck(
        ready=not errors,
        origin_iata=origin_iata,
        destination_iata=destination_iata,
        errors=errors,
    )