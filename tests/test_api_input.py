
import pytest
from pydantic import ValidationError

from pydantic_models.api_request import TravelRequestBody


THREAD_ID = "trip_" + "a" * 32


@pytest.mark.parametrize(
    "payload",
    [
        {
            "action": "start",
            "message": "Plan a trip to Italy.",
        },
        {
            "action": "reply",
            "message": "Two people.",
            "thread_id": THREAD_ID,
        },
        {
            "action": "cancel",
            "thread_id": THREAD_ID,
        },
    ],
)
def test_valid_session_actions(payload):
    request = TravelRequestBody.model_validate(payload)

    assert request.action.value == payload["action"]


@pytest.mark.parametrize(
    "payload",
    [
        # Cannot resume without a thread.
        {"action": "reply", "message": "Athens"},

        # Cannot reuse a thread for a new trip.
        {
            "action": "start",
            "message": "Plan a trip.",
            "thread_id": THREAD_ID,
        },

        # Cancel has no user message.
        {
            "action": "cancel",
            "message": "Hello",
            "thread_id": THREAD_ID,
        },

        # Start requires non-empty input.
        {"action": "start", "message": "   "},

        # Unknown action must be rejected.
        {"action": "restart", "message": "Italy"},
    ],
)
def test_invalid_session_actions(payload):
    with pytest.raises(ValidationError):
        TravelRequestBody.model_validate(payload)
