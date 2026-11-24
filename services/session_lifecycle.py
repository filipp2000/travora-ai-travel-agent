from typing import Any


class SessionConflictError(Exception):
    """The requested action is invalid for the current session."""


def _thread_config(thread_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def _is_pending(snapshot: Any) -> bool:
    """Check whether the checkpoint is waiting for user input."""

    return any(task.interrupts for task in snapshot.tasks)


def require_pending_session(
    graph: Any,
    thread_id: str,
    *,
    expected_interrupt_types: tuple[str, ...] | None = None,
) -> dict:
    """
    Validate that a thread can receive a clarification reply.

    No graph execution happens here.
    """

    config = _thread_config(thread_id)
    snapshot = graph.get_state(config)

    # Reject unknown, completed, or cancelled sessions.
    if (
        not snapshot.values
        or snapshot.values.get("session_cancelled", False)
        or not _is_pending(snapshot)
    ):
        raise SessionConflictError(
            "This trip is no longer waiting for a reply. Please start a new trip."
        )

    # Verify that the requested API action matches the
    # actual interrupted node, not just the thread ID.
    # so a user cannot reply to a trip brief when the workflow is waiting for a clarification.
    if expected_interrupt_types is not None:
        active_types = set()

        for task in snapshot.tasks:
            for item in task.interrupts:
                payload = getattr(item, "value", None)

                if isinstance(payload, dict):
                    active_types.add(payload.get("type"))

        if not active_types.intersection(expected_interrupt_types):
            raise SessionConflictError("This trip is waiting for a different action.")

    return config


def cancel_pending_session(
    graph: Any,
    thread_id: str,
) -> None:
    """
    Persistently mark an interrupted session as cancelled.

    This does not execute the graph or delete checkpoints.
    """

    config = _thread_config(thread_id)
    snapshot = graph.get_state(config)

    if not snapshot.values:
        raise SessionConflictError("Trip session was not found.")

    # Repeated cancellation is safe and idempotent.
    if snapshot.values.get("session_cancelled", False):
        return

    if not _is_pending(snapshot):
        raise SessionConflictError(
            "Only a trip waiting for user input can be cancelled."
        )

    # Save a cancellation marker in the persisted graph state.
    # Future reply attempts will be rejected before graph.invoke().
    graph.update_state(
        config,
        {"session_cancelled": True},
    )
