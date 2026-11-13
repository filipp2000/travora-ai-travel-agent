
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

    def __init__(self, *, pending=True, exists=True):
        self.values = (
            {"session_cancelled": False}
            if exists
            else {}
        )
        self.pending = pending
        self.update_calls = 0

    def get_state(self, config):
        # Represent a checkpoint waiting at interrupt().
        tasks = (
            [SimpleNamespace(interrupts=[object()])]
            if self.pending
            else []
        )

        return SimpleNamespace(
            values=self.values,
            tasks=tasks,
        )

    def update_state(self, config, changes):
        # Simulate writing a new persisted checkpoint state.
        self.values.update(changes)
        self.update_calls += 1


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


def test_cancel_marks_session_as_cancelled():
    graph = FakeGraph(pending=True)

    cancel_pending_session(graph, THREAD_ID)

    assert graph.values["session_cancelled"] is True
    assert graph.update_calls == 1

    # The cancellation marker prevents another resume.
    with pytest.raises(SessionConflictError):
        require_pending_session(graph, THREAD_ID)


def test_cancel_is_idempotent():
    graph = FakeGraph(pending=True)

    cancel_pending_session(graph, THREAD_ID)
    cancel_pending_session(graph, THREAD_ID)

    # The same session must not be updated twice.
    assert graph.update_calls == 1


def test_cannot_cancel_completed_session():
    graph = FakeGraph(pending=False)

    with pytest.raises(SessionConflictError):
        cancel_pending_session(graph, THREAD_ID)

    assert graph.update_calls == 0
