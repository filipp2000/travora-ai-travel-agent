from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator, model_validator

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


class SessionAction(StrEnum):
    START = "start"
    REPLY = "reply"
    CANCEL = "cancel"
    # actions for trip brief confirmation.
    BUILD = "build"
    EDIT = "edit"


# The TravelRequestBody model represents the request body for the API endpoint.
class TravelRequestBody(BaseModel):
    action: SessionAction

    # Cancel does not need a message, so this field is optional.
    message: TravelMessage | None = None
    thread_id: ThreadId | None = None

    @field_validator("message")
    @classmethod
    def validate_control_characters(
        cls,
        value: str | None,
    ) -> str | None:
        """Reject unsupported control characters."""

        # BUILD and CANCEL may have no message.
        if value is None:
            return None

        if any(
            (ord(char) < 32 and char not in "\n\t") or ord(char) == 127
            for char in value
        ):
            raise ValueError("Message contains unsupported control characters.")

        return value

    @model_validator(mode="after")
    def validate_session_action(self):
        """
        Validate valid combinations of session action,
        message and thread_id.
        """

        # Only START creates a new independent trip.
        if self.action == SessionAction.START:
            if self.message is None or self.thread_id is not None:
                raise ValueError("START requires a message and no thread_id.")

        # REPLY and EDIT need a message and an existing session.
        elif self.action in {
            SessionAction.REPLY,
            SessionAction.EDIT,
        }:
            if self.message is None or self.thread_id is None:
                raise ValueError("REPLY and EDIT require message and thread_id.")

        # BUILD and CANCEL are control operations.
        # They do not accept natural-language user messages.
        elif self.action in {
            SessionAction.BUILD,
            SessionAction.CANCEL,
        } and (self.thread_id is None or self.message is not None):
            raise ValueError(
                "BUILD and CANCEL require thread_id and must not contain a message."
            )

        # Return the validated model only after all checks.
        return self
