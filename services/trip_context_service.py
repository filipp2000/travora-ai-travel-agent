from pydantic_models.travel_request import (
    RequestIntent,
    TravelRequest,
)
from pydantic_models.trip_context import (
    TripContext,
    TripContextUpdate,
)


def merge_trip_context(
    current: TripContext,
    update: TripContextUpdate,
) -> TripContext:
    """Apply an extracted turn update without losing previous context."""

    changes = update.model_dump(
        exclude_none=True,
        exclude={"add_preferences", "remove_preferences", "capabilities"},
    )

    # Add newly requested capabilities without removing existing ones.
    if update.capabilities is not None:
        changes["capabilities"] = (
            # union operation
            current.capabilities | update.capabilities
    )
    # Changing the travel-time mode invalidates the old mode.
    if "travel_month" in changes:
        changes.update(
            start_date=None,
            end_date=None,
            dates_flexible=False,
        )

    elif "start_date" in changes or "end_date" in changes:
        changes.update(
            travel_month=None,
            dates_flexible=False,
        )

    elif changes.get("dates_flexible"):
        changes.update(
            start_date=None,
            end_date=None,
            travel_month=None,
        )

    # Remove explicitly unwanted preferences.
    removed = {item.strip().casefold() for item in update.remove_preferences}

    preferences = [
        item for item in current.preferences if item.casefold() not in removed
    ]

    # Add new preferences without duplicates.
    present = {item.casefold() for item in preferences}

    for raw in update.add_preferences:
        item = raw.strip()

        if item and item.casefold() not in present:
            preferences.append(item)
            present.add(item.casefold())

    changes["preferences"] = preferences

    # Revalidate the complete resulting context.
    return TripContext.model_validate(
        {
            **current.model_dump(),
            **changes,
        }
    )


def to_travel_request(
    context: TripContext,
    *,
    intent: RequestIntent,
) -> TravelRequest:
    """
    Convert accumulated trip context into the existing execution model.

    TripContext stores the user's planning information.
    TravelRequest is consumed by the current validation/routing workflow.
    """

    if intent != RequestIntent.TRAVEL:
        # Out-of-scope and unclear messages must not trigger research.
        return TravelRequest(
            intent=intent,
            capabilities=set(),
        )

    return TravelRequest(
        intent=intent,
        capabilities=set(context.capabilities),
        origin=context.origin,
        destination=context.destination,
        duration_days=context.duration_days,
        budget_amount=context.budget_amount,
        budget_currency=context.budget_currency,
        travelers=context.travelers,
        preferences=list(context.preferences),
    )