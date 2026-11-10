from datetime import date

import pytest

from pydantic_models.travel_request import TravelCapability
from pydantic_models.trip_context import BudgetScope, TripContext
from pydantic_models.trip_readiness import ReadinessIssue
from services.trip_readiness_service import (
    assess_trip_readiness,
    build_targeted_question,
)

# Fixed reference date keeps tests deterministic.
TODAY = date(2026, 11, 10)


def test_complete_trip_asks_only_for_dates_and_travelers():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        origin="Athens",
        destination="France",
        duration_days=5,
        budget_amount=2000,
        budget_currency="USD",
        budget_scope=BudgetScope.TOTAL_TRIP,
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert readiness.ready is False
    assert readiness.issues == [
        ReadinessIssue.MISSING_TRAVEL_PERIOD,
        ReadinessIssue.MISSING_TRAVELERS,
    ]

    question = build_targeted_question(readiness)

    assert "When would you like to travel?" in question
    assert "How many people" in question


def test_complete_trip_ready_with_month_and_travelers():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        origin="Athens",
        destination="France",
        duration_days=5,
        travel_month="2027-05",
        travelers=2,
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert readiness.ready is True
    assert readiness.issues == []
    assert build_targeted_question(readiness) is None


def test_hotel_only_preserves_short_flow():
    context = TripContext(
        capabilities={TravelCapability.HOTELS},
        destination="Rome",
        budget_amount=120,
        budget_currency="EUR",
        budget_scope=BudgetScope.PER_NIGHT,
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert readiness.ready is True


def test_flights_require_origin_period_and_travelers():
    context = TripContext(
        capabilities={TravelCapability.FLIGHTS},
        destination="Paris",
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert readiness.issues == [
        ReadinessIssue.MISSING_ORIGIN,
        ReadinessIssue.MISSING_TRAVEL_PERIOD,
        ReadinessIssue.MISSING_TRAVELERS,
    ]


def test_flexible_dates_allow_sample_itinerary():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        destination="Rome",
        duration_days=3,
        dates_flexible=True,
        travelers=1,
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert readiness.ready is True


def test_budget_requires_currency_and_scope():
    context = TripContext(
        capabilities={TravelCapability.HOTELS},
        destination="Rome",
        budget_amount=120,
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert readiness.issues == [
        ReadinessIssue.MISSING_BUDGET_CURRENCY,
        ReadinessIssue.MISSING_BUDGET_SCOPE,
    ]


def test_inconsistent_exact_dates_are_rejected():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        destination="Paris",
        travelers=1,
        duration_days=5,
        start_date=date(2026, 12, 9),
        end_date=date(2026, 12, 12),
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert ReadinessIssue.DURATION_DATE_MISMATCH in readiness.issues


def test_past_start_date_is_rejected():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        destination="Paris",
        travelers=1,
        duration_days=5,
        start_date=date(2026, 11, 1),
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert ReadinessIssue.PAST_START_DATE in readiness.issues


def test_questions_are_limited_to_two():
    context = TripContext(
        capabilities={TravelCapability.FLIGHTS},
    )

    readiness = assess_trip_readiness(context, today=TODAY)

    assert len(readiness.issues) > 2

    question = build_targeted_question(readiness)

    assert question == (
        "Which destination are you considering? Where will you depart from?"
    )


def test_invalid_max_questions_is_rejected():
    readiness = assess_trip_readiness(
        TripContext(),
        today=TODAY,
    )

    with pytest.raises(ValueError):
        build_targeted_question(
            readiness,
            max_questions=0,
        )
