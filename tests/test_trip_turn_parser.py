import json
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from llm.request_parser import extract_trip_turn
from pydantic_models.travel_request import (
    RequestIntent,
    TravelCapability,
)
from pydantic_models.trip_context import (
    BudgetScope,
    TripContext,
    TripContextUpdate,
    TripTurn,
)
from services.request_policy import apply_request_policy
from services.trip_context_service import (
    merge_trip_context,
    to_travel_request,
)


def mock_llm(*results: TripTurn) -> Mock:
    """Simulate structured LLM responses without using Groq."""

    llm = Mock()
    llm.with_structured_output.return_value.invoke.side_effect = list(results)

    return llm


def test_parser_extracts_one_structured_turn():
    expected = TripTurn(
        intent=RequestIntent.TRAVEL,
        update=TripContextUpdate(
            origin="Athens",
            travelers=1,
        ),
    )

    llm = mock_llm(expected)

    result = extract_trip_turn(
        latest_message="From Athens, traveling solo.",
        current_context=TripContext(destination="Netherlands"),
        llm=llm,
    )

    assert result == expected

    # Intent and extraction must happen in one LLM call.
    llm.with_structured_output.assert_called_once_with(
        TripTurn,
        method="json_schema",
    )
    llm.with_structured_output.return_value.invoke.assert_called_once()


@pytest.mark.parametrize(
    ("message", "pending_question", "raw_intent", "update"),
    [
        ("Hi", None, "greeting", {}),
        ("Hello there!", None, "greeting", {}),
        ("Good morning", None, "greeting", {}),
        (
            "Hi, plan a trip to London.",
            None,
            "travel",
            {"destination": "London", "capabilities": ["itinerary"]},
        ),
        ("I want to go somewhere.", None, "travel", {}),
        ("What?", None, "unclear", {}),
        (
            "Hi, Athens",
            "Where will you depart from?",
            "travel",
            {"origin": "Athens"},
        ),
    ],
    ids=[
        "hi",
        "hello",
        "good_morning",
        "mixed_greeting_and_request",
        "incomplete_travel",
        "unclear",
        "mixed_greeting_and_pending_details",
    ],
)
def test_structured_turn_supports_greeting_and_travel_contract(
    message, pending_question, raw_intent, update
):
    turn = TripTurn.model_validate({"intent": raw_intent, "update": update})
    llm = mock_llm(turn)

    result = extract_trip_turn(
        message, TripContext(), llm, pending_question=pending_question
    )

    assert result.intent.value == raw_intent
    assert result.update == TripContextUpdate.model_validate(update)
    llm.with_structured_output.assert_called_once_with(TripTurn, method="json_schema")
    llm.with_structured_output.return_value.invoke.assert_called_once()


def test_parser_receives_existing_context_and_pending_question():
    llm = mock_llm(
        TripTurn(
            intent=RequestIntent.TRAVEL,
            update=TripContextUpdate(origin="Athens"),
        )
    )

    extract_trip_turn(
        latest_message="Athens",
        current_context=TripContext(
            destination="Netherlands",
            duration_days=5,
        ),
        pending_question="Where will you depart from?",
        llm=llm,
    )

    messages = llm.with_structured_output.return_value.invoke.call_args.args[0]

    payload = json.loads(messages[1].content)

    assert payload["latest_user_message"] == "Athens"
    assert payload["current_trip_context"]["destination"] == "Netherlands"
    assert payload["pending_question"] == "Where will you depart from?"


def test_multiple_turns_preserve_existing_context():
    llm = mock_llm(
        TripTurn(
            intent=RequestIntent.TRAVEL,
            update=TripContextUpdate(
                capabilities={TravelCapability.ITINERARY},
                destination="Netherlands",
                duration_days=5,
                budget_amount=1200,
                budget_currency="EUR",
                budget_scope=BudgetScope.TOTAL_TRIP,
            ),
        ),
        TripTurn(
            intent=RequestIntent.TRAVEL,
            update=TripContextUpdate(
                origin="Athens",
                travelers=1,
                travel_month="2026-12",
                add_preferences=["museums", "architecture"],
            ),
        ),
    )

    context = TripContext()

    for message in [
        "Plan a 5-day trip to the Netherlands for €1200.",
        "From Athens, solo, in December 2026. I like museums and architecture.",
    ]:
        turn = extract_trip_turn(message, context, llm)

        # Only the deterministic service updates the stored context.
        context = merge_trip_context(context, turn.update)

    assert context.destination == "Netherlands"
    assert context.origin == "Athens"
    assert context.duration_days == 5
    assert context.travelers == 1
    assert context.travel_month == "2026-12"
    assert context.budget_amount == 1200
    assert context.preferences == ["museums", "architecture"]
    assert context.capabilities == {TravelCapability.ITINERARY}


def test_new_capabilities_do_not_replace_existing_ones():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
    )

    updated = merge_trip_context(
        context,
        TripContextUpdate(
            capabilities={TravelCapability.ACTIVITIES},
        ),
    )

    assert updated.capabilities == {
        TravelCapability.ITINERARY,
        TravelCapability.ACTIVITIES,
    }


def test_out_of_scope_cannot_create_executable_request():
    # Even if a classifier returns contradictory extracted details,
    # they must not become an executable travel request.
    context = TripContext(destination="Italy")

    request = to_travel_request(
        context,
        intent=RequestIntent.OUT_OF_SCOPE,
    )

    assert request.intent == RequestIntent.OUT_OF_SCOPE
    assert request.capabilities == set()
    assert request.destination is None


def test_existing_end_to_end_policy_still_applies():
    context = TripContext(
        capabilities={TravelCapability.ITINERARY},
        origin="Athens",
        destination="France",
        duration_days=5,
    )

    request = to_travel_request(
        context,
        intent=RequestIntent.TRAVEL,
    )

    normalized = apply_request_policy(request)

    assert normalized.capabilities == {
        TravelCapability.FLIGHTS,
        TravelCapability.HOTELS,
        TravelCapability.ITINERARY,
    }


def test_empty_message_is_rejected_before_llm_call():
    llm = Mock()

    with pytest.raises(ValueError):
        extract_trip_turn(
            latest_message="   ",
            current_context=TripContext(),
            llm=llm,
        )

    llm.with_structured_output.assert_not_called()


def test_null_preference_lists_are_normalized():
    """
    Regression test for the Groq response that caused
    the complete-trip request to fail.
    """

    raw_response = {
        "intent": "travel",
        "update": {
            "origin": "Athens",
            "destination": "France",
            "duration_days": 5,
            "budget_amount": 2000,
            "budget_currency": "USD",
            "capabilities": ["itinerary"],
            "add_preferences": None,
            "remove_preferences": None,
        },
    }

    # Simulate Pydantic parsing of the structured LLM response.
    turn = TripTurn.model_validate(raw_response)

    assert turn.update.add_preferences == []
    assert turn.update.remove_preferences == []

    # Other extracted fields must remain intact.
    assert turn.update.destination == "France"
    assert turn.update.duration_days == 5


def test_invalid_preference_type_is_still_rejected():
    """
    The validator should normalize null, not silently accept
    incorrectly typed preference values.
    """

    raw_response = {
        "intent": "travel",
        "update": {
            "add_preferences": "museums",
        },
    }

    with pytest.raises(ValidationError):
        TripTurn.model_validate(raw_response)
