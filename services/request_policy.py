from pydantic_models.travel_request import (
    TravelCapability,
    TravelRequest,
)


def apply_request_policy(
    request: TravelRequest,
) -> TravelRequest:
    """
    Apply deterministic Travora product rules after LLM parsing.

    In the current Travora scope, an itinerary request that
    includes both an origin and a destination represents an
    end-to-end trip-planning request.

    End-to-end trip planning requires:
    - transport planning (flights)
    - accommodation planning (hotels)
    - itinerary generation

    This rule prevents routing correctness from depending
    entirely on probabilistic LLM capability classification.
    """

    capabilities = set(
        request.capabilities
    )

    is_end_to_end_trip = (
        TravelCapability.ITINERARY
        in capabilities
        and request.origin is not None
        and request.destination is not None
    )

    if is_end_to_end_trip:
        capabilities.update(
            {
                TravelCapability.FLIGHTS,
                TravelCapability.HOTELS,
            }
        )

    return request.model_copy(
        update={
            "capabilities": capabilities
        }
    )