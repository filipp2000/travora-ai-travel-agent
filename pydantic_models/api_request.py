from typing import Annotated

from pydantic import (
    BaseModel,
    StringConstraints,
    field_validator,
)

# Using Pydantic constraints to enforce validation rules for the TravelRequestBody model.
# FastApi returns a 422 error if the request body does not conform to these constraints.

TravelMessage = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2000,
    ),
]

ThreadId = Annotated[
    str,
    StringConstraints(
        min_length=37,
        max_length=37,
        pattern=r"^trip_[0-9a-f]{32}$",
    ),
]


class TravelRequestBody(BaseModel):
    message: TravelMessage
    thread_id: ThreadId | None = None

    @field_validator("message")
    @classmethod
    def validate_control_characters(cls, value: str) -> str:
        if any(
            (ord(char) < 32 and char not in "\n\t")
            or ord(char) == 127
            for char in value
        ):
            raise ValueError(
                "Message contains unsupported control characters."
            )

        return value