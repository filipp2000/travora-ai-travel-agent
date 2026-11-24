
from pydantic_models.travel_request import TravelRequest
from pydantic_models.trip_context import TripContext


def build_trip_brief(
    context: TripContext,
    request: TravelRequest,
) -> dict:
    """
    Build a user-facing summary from validated trip context.

    No LLM calls, database queries or external APIs.
    """

    # Dates remain exactly as provided by the user.
    # We do not invent a departure date from a travel month.
    if context.start_date and context.end_date:
        travel_period = (
            f"{context.start_date.isoformat()} "
            f"to {context.end_date.isoformat()}"
        )

    elif context.start_date:
        travel_period = context.start_date.isoformat()

    elif context.travel_month:
        travel_period = context.travel_month

    elif context.dates_flexible:
        travel_period = "Flexible dates"

    else:
        travel_period = None

    # Budget amount, currency and scope stay together.
    # Never reinterpret a total-trip budget as per-night.
    budget = None

    if context.budget_amount is not None:
        budget = {
            "amount": context.budget_amount,
            "currency": context.budget_currency,
            "scope": (
                context.budget_scope.value
                if context.budget_scope
                else None
            ),
        }

    return {
        "origin": context.origin,
        "destination": context.destination,
        "duration_days": context.duration_days,
        "travel_period": travel_period,
        "dates_flexible": context.dates_flexible,
        "travelers": context.travelers,
        "budget": budget,
        "preferences": list(context.preferences),

        # Show what the EXECUTION policy will actually run,
        # not only the capabilities originally extracted by the LLM.
        "capabilities": sorted(
            capability.value
            for capability in request.capabilities
        ),
    }
