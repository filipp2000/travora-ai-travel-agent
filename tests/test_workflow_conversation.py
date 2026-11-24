from datetime import date
from functools import partial
from unittest.mock import Mock

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from pydantic_models.travel_request import (
    RequestIntent,
    TravelCapability,
)
from pydantic_models.trip_context import (
    BudgetScope,
    TripContext,
    TripContextUpdate,
    TripTurn,
)
from workflow.nodes import (
    ask_trip_details_node,
    assess_trip_readiness_node,
    present_trip_brief_node,
    scope_response_node,
    understand_request_node,
)
from workflow.routing import (
    route_after_brief_decision,
    route_after_readiness,
    route_after_understanding,
)
from workflow.state import TravelState

# Fixed reference date for reproducible readiness tests.
TODAY = date(2026, 11, 10)


# ---------------------------------------------------------
# Test graph configuration
# ---------------------------------------------------------


def build_test_graph(llm: Mock):
    """
    Compile the conversational workflow with in-memory checkpoints.

    Real conversational nodes and routing functions are used.
    LLM responses and execution services are mocked.
    """

    graph = StateGraph(TravelState)

    graph.add_node(
        "understand_request",
        partial(understand_request_node, llm=llm),
    )

    graph.add_node(
        "assess_trip_readiness",
        partial(assess_trip_readiness_node, today=TODAY),
    )

    graph.add_node(
        "ask_trip_details",
        ask_trip_details_node,
    )

    graph.add_node(
        "present_trip_brief",
        present_trip_brief_node,
    )

    graph.add_node(
        "scope_response",
        scope_response_node,
    )

    # Stub the execution boundary.
    # Reaching this node means the user approved the trip.
    graph.add_node(
        "check_request",
        lambda state: {"final_answer": "READY"},
    )

    graph.add_edge(
        START,
        "understand_request",
    )

    graph.add_conditional_edges(
        "understand_request",
        route_after_understanding,
        [
            "assess_trip_readiness",
            "scope_response",
        ],
    )

    # Readiness now leads to confirmation, not execution.
    graph.add_conditional_edges(
        "assess_trip_readiness",
        route_after_readiness,
        [
            "ask_trip_details",
            "present_trip_brief",
        ],
    )

    graph.add_edge(
        "ask_trip_details",
        "understand_request",
    )

    # EDIT returns to extraction.
    # BUILD continues to execution validation.
    graph.add_conditional_edges(
        "present_trip_brief",
        route_after_brief_decision,
        [
            "understand_request",
            "check_request",
        ],
    )

    graph.add_edge("check_request", END)
    graph.add_edge("scope_response", END)

    # No external database connection is required.
    return graph.compile(checkpointer=InMemorySaver())


# ---------------------------------------------------------
# Multi-turn collection and approval
# ---------------------------------------------------------


def test_multi_turn_collection_preserves_context():
    first_turn = TripTurn(
        intent=RequestIntent.TRAVEL,
        update=TripContextUpdate(
            capabilities={TravelCapability.ITINERARY},
            origin="Athens",
            destination="France",
            duration_days=5,
            budget_amount=2000,
            budget_currency="USD",
            budget_scope=BudgetScope.TOTAL_TRIP,
        ),
    )

    second_turn = TripTurn(
        intent=RequestIntent.TRAVEL,
        update=TripContextUpdate(
            travelers=2,
            travel_month="2027-05",
        ),
    )

    llm = Mock()

    llm.with_structured_output.return_value.invoke.side_effect = [
        first_turn,
        second_turn,
    ]

    graph = build_test_graph(llm)

    config = {
        "configurable": {
            "thread_id": "test-conversation-1",
        }
    }

    # Step 1: Start an incomplete trip request.
    first_result = graph.invoke(
        {
            "user_query": ("Plan a 5-day trip to France from Athens under $2000."),
            "trip_context": TripContext(),
        },
        config=config,
    )

    assert "__interrupt__" in first_result

    first_payload = first_result["__interrupt__"][0].value

    assert first_payload["type"] == "trip_details"
    assert "When would you like to travel?" in first_payload["question"]
    assert "How many people" in first_payload["question"]

    # Step 2: Resume the same thread with missing details.
    second_result = graph.invoke(
        Command(resume="Two people, in May 2027."),
        config=config,
    )

    # Readiness is satisfied, but confirmation is still required.
    assert "__interrupt__" in second_result

    brief_payload = second_result["__interrupt__"][0].value

    assert brief_payload["type"] == "trip_brief"
    assert brief_payload["brief"]["travelers"] == 2
    assert brief_payload["brief"]["travel_period"] == "2027-05"

    # The execution boundary must not have been reached yet.
    assert second_result.get("final_answer") != "READY"

    # Step 3: Explicitly approve the trip brief.
    final_result = graph.invoke(
        Command(resume={"action": "build"}),
        config=config,
    )

    assert final_result["final_answer"] == "READY"

    # Verify accumulated context survived all interruptions.
    context = TripContext.model_validate(final_result["trip_context"])

    assert context.origin == "Athens"
    assert context.destination == "France"
    assert context.duration_days == 5
    assert context.budget_amount == 2000
    assert context.budget_currency == "USD"
    assert context.budget_scope == BudgetScope.TOTAL_TRIP
    assert context.travel_month == "2027-05"
    assert context.travelers == 2

    # Two user messages require two extraction calls.
    # BUILD itself must not trigger another extraction.
    assert llm.with_structured_output.return_value.invoke.call_count == 2


# ---------------------------------------------------------
# Trip brief editing
# ---------------------------------------------------------


def test_edit_requires_new_brief_confirmation():
    first_turn = TripTurn(
        intent=RequestIntent.TRAVEL,
        update=TripContextUpdate(
            capabilities={TravelCapability.ITINERARY},
            origin="Athens",
            destination="France",
            duration_days=5,
            travel_month="2027-05",
            travelers=2,
        ),
    )

    edited_turn = TripTurn(
        intent=RequestIntent.TRAVEL,
        update=TripContextUpdate(
            duration_days=7,
        ),
    )

    llm = Mock()

    llm.with_structured_output.return_value.invoke.side_effect = [
        first_turn,
        edited_turn,
    ]

    graph = build_test_graph(llm)

    config = {
        "configurable": {
            "thread_id": "test-brief-edit",
        }
    }

    # Step 1: Complete initial context reaches confirmation.
    first_result = graph.invoke(
        {
            "user_query": (
                "Plan a 5-day trip to France from Athens for two people in May 2027."
            ),
            "trip_context": TripContext(),
        },
        config=config,
    )

    first_brief = first_result["__interrupt__"][0].value

    assert first_brief["type"] == "trip_brief"
    assert first_brief["brief"]["duration_days"] == 5
    assert first_result.get("final_answer") != "READY"

    # Step 2: Edit the trip instead of approving it.
    edited_result = graph.invoke(
        Command(
            resume={
                "action": "edit",
                "message": "Actually, make it 7 days.",
            }
        ),
        config=config,
    )

    # The graph must present a new brief after the edit.
    updated_brief = edited_result["__interrupt__"][0].value

    assert updated_brief["type"] == "trip_brief"
    assert updated_brief["brief"]["duration_days"] == 7

    # Unchanged trip requirements must be preserved.
    assert updated_brief["brief"]["origin"] == "Athens"
    assert updated_brief["brief"]["destination"] == "France"
    assert updated_brief["brief"]["travelers"] == 2
    assert updated_brief["brief"]["travel_period"] == "2027-05"

    # Editing does not authorize execution.
    assert edited_result.get("final_answer") != "READY"

    # Step 3: Approve the updated brief.
    final_result = graph.invoke(
        Command(resume={"action": "build"}),
        config=config,
    )

    assert final_result["final_answer"] == "READY"

    context = TripContext.model_validate(final_result["trip_context"])

    assert context.duration_days == 7

    # One extraction for the initial message and one for the edit.
    assert llm.with_structured_output.return_value.invoke.call_count == 2


# ---------------------------------------------------------
# Intent guardrails
# ---------------------------------------------------------


def test_out_of_scope_initial_request_finishes_without_collection():
    llm = Mock()

    llm.with_structured_output.return_value.invoke.return_value = TripTurn(
        intent=RequestIntent.OUT_OF_SCOPE,
        update=TripContextUpdate(),
    )

    graph = build_test_graph(llm)

    result = graph.invoke(
        {
            "user_query": "What is Generative AI?",
            "trip_context": TripContext(),
        },
        config={
            "configurable": {
                "thread_id": "test-out-of-scope",
            }
        },
    )

    # Unrelated requests must not enter collection or confirmation.
    assert not result.get("__interrupt__")
    assert "Travora specializes" in result["final_answer"]
