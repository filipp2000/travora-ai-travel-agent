from pydantic_models.travel_request import TravelCapability
from pydantic_models.trip_context import (
    BudgetScope,
    TripContext,
    TripContextUpdate,
)
from services.trip_context_service import merge_trip_context


def test_context_accumulates_information_across_turns():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
    )

    first_turn = TripContextUpdate(
        destination="Netherlands",
        duration_days=5,
        budget_amount=1200,
        budget_currency="EUR",
        budget_scope=BudgetScope.TOTAL_TRIP,
    )

    context = merge_trip_context(context, first_turn)

    second_turn = TripContextUpdate(
        origin="Athens",
        travelers=1,
        travel_month="2026-12",
    )

    context = merge_trip_context(context, second_turn)

    third_turn = TripContextUpdate(
        add_preferences=["Museums", "Architecture"],
    )

    context = merge_trip_context(context, third_turn)

    assert context.origin == "Athens"
    assert context.destination == "Netherlands"
    assert context.duration_days == 5
    assert context.travel_month == "2026-12"
    assert context.travelers == 1
    assert context.budget_amount == 1200
    assert context.budget_scope == BudgetScope.TOTAL_TRIP
    assert context.preferences == ["Museums", "Architecture"]


def test_explicit_correction_replaces_only_target_field():
    context = TripContext(
        origin="Athens",
        destination="Italy",
        travelers=2,
        budget_amount=1500,
    )

    updated = merge_trip_context(
        context,
        TripContextUpdate(origin="Thessaloniki"),
    )

    assert updated.origin == "Thessaloniki"
    assert updated.destination == "Italy"
    assert updated.travelers == 2
    assert updated.budget_amount == 1500


def test_preferences_can_be_added_and_removed():
    context = TripContext(
        preferences=["Museums", "Nightlife"],
    )

    updated = merge_trip_context(
        context,
        TripContextUpdate(
            add_preferences=["Architecture", "museums"],
            remove_preferences=["nightlife"],
        ),
    )

    assert updated.preferences == ["Museums", "Architecture"]


def test_exact_dates_replace_month_level_timing():
    context = TripContext(
        travel_month="2026-12",
    )

    updated = merge_trip_context(
        context,
        TripContextUpdate(
            start_date="2026-12-09",
            end_date="2026-12-13",
        ),
    )

    assert updated.start_date.isoformat() == "2026-12-09"
    assert updated.end_date.isoformat() == "2026-12-13"
    assert updated.travel_month is None


def test_missing_fields_do_not_clear_existing_values():
    context = TripContext(
        destination="Rome",
        budget_amount=800,
        budget_currency="EUR",
    )

    updated = merge_trip_context(
        context,
        TripContextUpdate(travelers=2),
    )

    assert updated.destination == "Rome"
    assert updated.budget_amount == 800
    assert updated.budget_currency == "EUR"
    assert updated.travelers == 2
