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
        if value is None:
            return None

        if any(
            (ord(char) < 32 and char not in "\n\t")
            or ord(char) == 127
            for char in value
        ):
            raise ValueError(
                "Message contains unsupported control characters."
            )

        return value

    @model_validator(mode="after")
    def validate_session_action(self):
        """
        Enforce valid action/message/thread combinations
        before the request reaches the backend.
        """

        if self.action in {
            SessionAction.START,
            SessionAction.REPLY,
        } and self.message is None:
            raise ValueError(
                "A message is required for start and reply."
            )

        if self.action == SessionAction.START:
            # New trips must not reuse existing thread IDs.
            if self.thread_id is not None:
                raise ValueError(
                    "New trips must not provide a thread_id."
                )

        elif self.action == SessionAction.REPLY:
            # A clarification can only target a known thread.
            if self.thread_id is None:
                raise ValueError(
                    "A thread_id is required for reply."
                )

        elif self.action == SessionAction.CANCEL:
            if self.thread_id is None:
                raise ValueError(
                    "A thread_id is required for cancel."
                )

            # Cancel is a control operation, not a user message.
            if self.message is not None:
                raise ValueError(
                    "Cancel must not contain a message."
                )

        return self
