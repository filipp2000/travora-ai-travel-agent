from types import SimpleNamespace

import pytest

from services.session_lifecycle import (
    SessionConflictError,
    cancel_pending_session,
    require_pending_session,
)

THREAD_ID = "trip_" + "b" * 32


class FakeGraph:
    """Small test double for LangGraph checkpoint operations."""

    def __init__(
        self,
        *,
        pending=True,
        exists=True,
        interrupt_type="trip_details",
    ):
        self.values = {"session_cancelled": False} if exists else {}

        self.pending = pending
        self.interrupt_type = interrupt_type
        self.update_calls = 0

    def get_state(self, config):
        # Simulate a LangGraph checkpoint with a typed interrupt.
        tasks = (
            [
                SimpleNamespace(
                    interrupts=[SimpleNamespace(value={"type": self.interrupt_type})]
                )
            ]
            if self.pending
            else []
        )

        return SimpleNamespace(
            values=self.values,
            tasks=tasks,
        )

    def update_state(self, config, changes):
        # Simulate writing an updated checkpoint.
        self.values.update(changes)
        self.update_calls += 1


# ---------------------------------------------------------
# Session availability
# ---------------------------------------------------------


def test_active_pending_session_can_resume():
    graph = FakeGraph(pending=True)

    config = require_pending_session(graph, THREAD_ID)

    assert config["configurable"]["thread_id"] == THREAD_ID


def test_completed_session_cannot_resume():
    graph = FakeGraph(pending=False)

    with pytest.raises(SessionConflictError):
        require_pending_session(graph, THREAD_ID)


def test_unknown_session_cannot_resume():
    graph = FakeGraph(exists=False)

    with pytest.raises(SessionConflictError):
        require_pending_session(graph, THREAD_ID)


# ---------------------------------------------------------
# Session cancellation
# ---------------------------------------------------------


def test_cancel_marks_session_as_cancelled():
    graph = FakeGraph(pending=True)

    cancel_pending_session(graph, THREAD_ID)

    assert graph.values["session_cancelled"] is True
    assert graph.update_calls == 1

    # Cancelled sessions must reject subsequent replies.
    with pytest.raises(SessionConflictError):
        require_pending_session(graph, THREAD_ID)


def test_cancel_is_idempotent():
    graph = FakeGraph(pending=True)

    cancel_pending_session(graph, THREAD_ID)
    cancel_pending_session(graph, THREAD_ID)

    # Repeated cancellation must not write another checkpoint.
    assert graph.update_calls == 1


def test_cannot_cancel_completed_session():
    graph = FakeGraph(pending=False)

    with pytest.raises(SessionConflictError):
        cancel_pending_session(graph, THREAD_ID)

    assert graph.update_calls == 0


# ---------------------------------------------------------
# Action-to-interrupt matching
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "interrupt_type, expected_types",
    [
        ("trip_details", ("trip_details", "clarification")),
        ("clarification", ("trip_details", "clarification")),
        ("trip_brief", ("trip_brief",)),
    ],
    ids=[
        "reply_to_trip_details",
        "reply_to_legacy_clarification",
        "build_or_edit_trip_brief",
    ],
)
def test_matching_interrupt_allows_resume(
    interrupt_type,
    expected_types,
):
    graph = FakeGraph(
        pending=True,
        interrupt_type=interrupt_type,
    )

    config = require_pending_session(
        graph,
        THREAD_ID,
        expected_interrupt_types=expected_types,
    )

    assert config["configurable"]["thread_id"] == THREAD_ID


@pytest.mark.parametrize(
    "interrupt_type, expected_types",
    [
        ("trip_details", ("trip_brief",)),
        ("trip_brief", ("trip_details", "clarification")),
    ],
    ids=[
        "build_or_edit_before_readiness",
        "reply_to_confirmation_gate",
    ],
)
def test_mismatched_interrupt_rejects_resume(
    interrupt_type,
    expected_types,
):
    graph = FakeGraph(
        pending=True,
        interrupt_type=interrupt_type,
    )

    # The requested action must not bypass the current gate.
    with pytest.raises(SessionConflictError):
        require_pending_session(
            graph,
            THREAD_ID,
            expected_interrupt_types=expected_types,
        )


def test_cancel_is_allowed_during_trip_brief_confirmation():
    graph = FakeGraph(
        pending=True,
        interrupt_type="trip_brief",
    )

    cancel_pending_session(graph, THREAD_ID)

    assert graph.values["session_cancelled"] is True

    # Cancellation also prevents future BUILD or EDIT actions.
    with pytest.raises(SessionConflictError):
        require_pending_session(
            graph,
            THREAD_ID,
            expected_interrupt_types=("trip_brief",),
        )
