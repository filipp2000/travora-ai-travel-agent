import pytest
from pydantic import ValidationError

from pydantic_models.api_request import SessionAction, TravelRequestBody


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "x" * 2001,
        "hello\x00world",
    ],
)
def test_invalid_input_is_rejected(message: str):
    with pytest.raises(ValidationError):
        TravelRequestBody(message=message)


def test_valid_travel_input_is_accepted():
    # A new independent travel request must explicitly
    # declare the START session action.
    request = TravelRequestBody(
        action=SessionAction.START,
        message="  Find hotels in Rome.  ",
    )

    # Input normalization should still remove surrounding spaces.
    assert request.message == "Find hotels in Rome."

    # START must not reuse an existing conversation thread.
    assert request.thread_id is None


def test_invalid_thread_id_is_rejected():
    with pytest.raises(ValidationError):
        TravelRequestBody(
            message="Find hotels in Rome",
            thread_id="invalid-thread",
        )
