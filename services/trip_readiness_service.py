from datetime import date

from pydantic_models.travel_request import TravelCapability
from pydantic_models.trip_context import TripContext
from pydantic_models.trip_readiness import (
    ReadinessIssue,
    TripReadiness,
)

# Fixed, deterministic questions for each readiness issue.
# We can later change the wording without changing business rules.
_QUESTIONS: dict[ReadinessIssue, str] = {
    ReadinessIssue.MISSING_CAPABILITY: "Would you like an itinerary, flights, hotels, or activities?",
    ReadinessIssue.MISSING_DESTINATION: "Which destination are you considering?",
    ReadinessIssue.MISSING_ORIGIN: "Where will you depart from?",
    ReadinessIssue.MISSING_DURATION: "How many days should the trip last?",
    ReadinessIssue.MISSING_TRAVEL_PERIOD: "When would you like to travel? Give exact dates, "
    "a month and year, or tell me your dates are flexible.",
    ReadinessIssue.MISSING_TRAVEL_YEAR: "Which year do you mean for that month?",
    ReadinessIssue.MISSING_START_DATE: "What is the trip's start date?",
    ReadinessIssue.MISSING_TRAVELERS: "How many people are traveling?",
    ReadinessIssue.MISSING_BUDGET_CURRENCY: "Which currency is your budget in?",
    ReadinessIssue.MISSING_BUDGET_SCOPE: "Is that budget for the whole trip or per night?",
    ReadinessIssue.INVALID_DATE_RANGE: "Your end date is before your start date. "
    "What dates should I use?",
    ReadinessIssue.DURATION_DATE_MISMATCH: "The dates and trip duration don't match. "
    "Which should I change?",
    ReadinessIssue.PAST_START_DATE: "The start date has already passed. "
    "What new date should I use?",
    ReadinessIssue.PAST_TRAVEL_MONTH: "That month is in the past. "
    "Which future month should I use?",
}


def assess_trip_readiness(
    context: TripContext,
    *,
    today: date,
) -> TripReadiness:
    """
    Determine whether the trip has enough valid information.

    Pure deterministic business logic:
    - No LLM calls
    - No external APIs
    - No modifications to the input context
    """

    issues: list[ReadinessIssue] = []

    capabilities = context.capabilities

    needs_flights = TravelCapability.FLIGHTS in capabilities
    needs_itinerary = TravelCapability.ITINERARY in capabilities

    # -------------------------------------------------
    # 1. General trip requirements
    # -------------------------------------------------

    if not capabilities:
        issues.append(ReadinessIssue.MISSING_CAPABILITY)

    if not context.destination or not context.destination.strip():
        issues.append(ReadinessIssue.MISSING_DESTINATION)

    # Only flight planning needs a departure location.
    if needs_flights and (not context.origin or not context.origin.strip()):
        issues.append(ReadinessIssue.MISSING_ORIGIN)

    # A day-by-day itinerary requires a trip duration.
    if needs_itinerary and context.duration_days is None:
        issues.append(ReadinessIssue.MISSING_DURATION)

    # -------------------------------------------------
    # 2. Travel period requirements
    # -------------------------------------------------

    needs_travel_period = needs_itinerary or needs_flights

    if context.end_date is not None and context.start_date is None:
        issues.append(ReadinessIssue.MISSING_START_DATE)

    elif needs_travel_period:
        has_period = bool(
            context.start_date or context.travel_month or context.dates_flexible
        )

        if not has_period:
            issues.append(ReadinessIssue.MISSING_TRAVEL_PERIOD)

        # A month without a year is insufficient for
        # time-specific travel planning.
        elif context.travel_month and len(context.travel_month) == 2:
            issues.append(ReadinessIssue.MISSING_TRAVEL_YEAR)

    # -------------------------------------------------
    # 3. Date consistency checks
    # -------------------------------------------------

    if context.start_date is not None and context.start_date < today:
        issues.append(ReadinessIssue.PAST_START_DATE)

    if context.start_date is not None and context.end_date is not None:
        if context.end_date < context.start_date:
            issues.append(ReadinessIssue.INVALID_DATE_RANGE)

        elif context.duration_days is not None:
            # Inclusive calendar-day duration:
            # December 9–13 = 5 days, 4 nights.
            calendar_days = (context.end_date - context.start_date).days + 1

            if calendar_days != context.duration_days:
                issues.append(ReadinessIssue.DURATION_DATE_MISMATCH)

    if (
        context.travel_month
        and len(context.travel_month) == 7
        and context.travel_month < today.strftime("%Y-%m")
    ):
        # YYYY-MM can be compared lexicographically to determine if it's in the past.
        issues.append(ReadinessIssue.PAST_TRAVEL_MONTH)

    # -------------------------------------------------
    # 4. Travelers
    # -------------------------------------------------

    if (needs_itinerary or needs_flights) and context.travelers is None:
        issues.append(ReadinessIssue.MISSING_TRAVELERS)

    # -------------------------------------------------
    # 5. Budget interpretation
    # -------------------------------------------------

    # Budget itself is optional. When specified, its
    # currency and scope must be unambiguous.
    if context.budget_amount is not None:
        if not context.budget_currency:
            issues.append(ReadinessIssue.MISSING_BUDGET_CURRENCY)

        if context.budget_scope is None:
            issues.append(ReadinessIssue.MISSING_BUDGET_SCOPE)

    # Ready only when no unresolved issues remain.
    return TripReadiness(
        ready=not issues,
        issues=issues,
    )


def build_targeted_question(
    readiness: TripReadiness,
    *,
    max_questions: int = 2,
) -> str | None:
    """
    Convert readiness issues into a small group of questions.

    The user can answer multiple missing fields in one turn.
    """

    if max_questions < 1:
        raise ValueError("max_questions must be at least 1")

    if readiness.ready:
        return None

    # Ask only a limited number of questions per turn.
    selected_issues = readiness.issues[:max_questions]

    return " ".join(
        _QUESTIONS[issue]
        for issue in selected_issues
    )
