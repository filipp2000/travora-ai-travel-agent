import pytest
from pydantic import ValidationError

from pydantic_models.api_request import TravelRequestBody


THREAD_ID = "trip_" + "a" * 32


# ---------------------------------------------------------
# Valid session actions
# ---------------------------------------------------------


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
        {
            # BUILD is an explicit approval without a message.
            "action": "build",
            "thread_id": THREAD_ID,
        },
        {
            # EDIT requires a correction message.
            "action": "edit",
            "thread_id": THREAD_ID,
            "message": "Make it 7 days.",
        },
    ],
    ids=[
        "start",
        "reply",
        "cancel",
        "build",
        "edit",
    ],
)
def test_valid_session_actions(payload):
    request = TravelRequestBody.model_validate(payload)

    assert request.action.value == payload["action"]


# ---------------------------------------------------------
# Invalid session actions
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        # REPLY requires an existing thread.
        {
            "action": "reply",
            "message": "Athens",
        },
        # START must not reuse an existing thread.
        {
            "action": "start",
            "message": "Plan a trip.",
            "thread_id": THREAD_ID,
        },
        # CANCEL must not contain a message.
        {
            "action": "cancel",
            "message": "Hello",
            "thread_id": THREAD_ID,
        },
        # Empty messages are not valid.
        {
            "action": "start",
            "message": "   ",
        },
        # Unknown session actions must be rejected.
        {
            "action": "restart",
            "message": "Italy",
        },
        # BUILD requires an existing thread.
        {
            "action": "build",
        },
        # BUILD must not accept natural-language approval.
        {
            "action": "build",
            "thread_id": THREAD_ID,
            "message": "Yes",
        },
        # EDIT requires a correction message.
        {
            "action": "edit",
            "thread_id": THREAD_ID,
        },
    ],
    ids=[
        "reply_without_thread",
        "start_with_existing_thread",
        "cancel_with_message",
        "empty_message",
        "unknown_action",
        "build_without_thread",
        "build_with_message",
        "edit_without_message",
    ],
)
def test_invalid_session_actions(payload):
    with pytest.raises(ValidationError):
        TravelRequestBody.model_validate(payload)
