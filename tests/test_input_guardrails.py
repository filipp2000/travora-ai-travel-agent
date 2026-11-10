import pytest
from pydantic import ValidationError

from pydantic_models.api_request import TravelRequestBody


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
    request = TravelRequestBody(
        message="  Find hotels in Rome.  "
    )

    assert request.message == "Find hotels in Rome."


def test_invalid_thread_id_is_rejected():
    with pytest.raises(ValidationError):
        TravelRequestBody(
            message="Find hotels in Rome",
            thread_id="invalid-thread",
        )