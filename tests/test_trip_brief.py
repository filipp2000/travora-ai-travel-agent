from pydantic_models.travel_request import (
    RequestIntent,
    TravelCapability,
)
from pydantic_models.trip_context import (
    BudgetScope,
    TripContext,
)
from services.request_policy import apply_request_policy
from services.trip_brief_service import build_trip_brief
from services.trip_context_service import to_travel_request


def test_trip_brief_reflects_execution_capabilities():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        origin="Athens",
        destination="France",
        duration_days=5,
        travel_month="2027-05",
        travelers=2,
        budget_amount=2000,
        budget_currency="USD",
        budget_scope=BudgetScope.TOTAL_TRIP,
    )

    # Reproduce the execution contract used by LangGraph.
    request = apply_request_policy(
        to_travel_request(
            context,
            intent=RequestIntent.TRAVEL,
        )
    )

    brief = build_trip_brief(context, request)

    assert brief["origin"] == "Athens"
    assert brief["destination"] == "France"
    assert brief["duration_days"] == 5
    assert brief["travel_period"] == "2027-05"
    assert brief["travelers"] == 2

    # Preserve the original budget semantics.
    assert brief["budget"] == {
        "amount": 2000,
        "currency": "USD",
        "scope": "total_trip",
    }

    # The brief must reflect the effective execution capabilities,
    # including those added by the deterministic request policy.
    assert brief["capabilities"] == [
        "flights",
        "hotels",
        "itinerary",
    ]


def test_flexible_dates_do_not_generate_fake_dates():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        destination="Italy",
        duration_days=5,
        travelers=1,
        dates_flexible=True,
    )

    request = to_travel_request(
        context,
        intent=RequestIntent.TRAVEL,
    )

    brief = build_trip_brief(context, request)

    # Do not invent exact dates or a budget.
    assert brief["travel_period"] == "Flexible dates"
    assert brief["dates_flexible"] is True
    assert brief["budget"] is None
