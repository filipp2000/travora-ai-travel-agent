
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
    scope_response_node,
    understand_request_node,
)
from workflow.routing import (
    route_after_readiness,
    route_after_understanding,
)
from workflow.state import TravelState

TODAY = date(2026, 11, 12)


def build_test_graph(llm: Mock):
    """
    Compile only the conversational part of the workflow.

    No Groq calls, travel providers or PostgreSQL access.
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

    graph.add_node("scope_response", scope_response_node)

    # This node represents the boundary to the execution workflow.
    # Reaching it means collection finished successfully.
    graph.add_node(
        "check_request",
        lambda state: {"final_answer": "READY"},
    )

    graph.add_edge(START, "understand_request")

    graph.add_conditional_edges(
        "understand_request",
        route_after_understanding,
        ["assess_trip_readiness", "scope_response"],
    )

    graph.add_conditional_edges(
        "assess_trip_readiness",
        route_after_readiness,
        ["ask_trip_details", "check_request"],
    )

    graph.add_edge("ask_trip_details", "understand_request")
    graph.add_edge("check_request", END)
    graph.add_edge("scope_response", END)

    # In-memory checkpointing verifies interrupt/resume semantics
    # without requiring a real Neon database.
    return graph.compile(checkpointer=InMemorySaver())


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

    # First turn: missing travel period and travelers.
    first_result = graph.invoke(
        {
            "user_query": (
                "Plan a 5-day trip to France "
                "from Athens under $2000."
            ),
            "trip_context": TripContext(),
        },
        config=config,
    )

    # The workflow must pause instead of reaching research.
    assert "__interrupt__" in first_result

    question = first_result["__interrupt__"][0].value["question"]

    assert "When would you like to travel?" in question
    assert "How many people" in question

    # Resume the SAME thread with the user's clarification.
    final_result = graph.invoke(
        Command(resume="Two people, in May 2027."),
        config=config,
    )

    assert final_result["final_answer"] == "READY"

    context = TripContext.model_validate(
        final_result["trip_context"]
    )

    # Previously collected details must survive the interruption.
    assert context.origin == "Athens"
    assert context.destination == "France"
    assert context.duration_days == 5
    assert context.budget_amount == 2000
    assert context.travel_month == "2027-05"
    assert context.travelers == 2

    # Exactly one extraction call per user turn.
    assert (
        llm.with_structured_output.return_value.invoke.call_count
        == 2
    )


def test_out_of_scope_initial_request_finishes_without_collection():
    llm = Mock()

    llm.with_structured_output.return_value.invoke.return_value = (
        TripTurn(
            intent=RequestIntent.OUT_OF_SCOPE,
            update=TripContextUpdate(),
        )
    )

    graph = build_test_graph(llm)

    result = graph.invoke(
        {
            "user_query": "What is Generative AI?",
            "trip_context": TripContext(),
        },
        config={
            "configurable": {
                "thread_id": "test-conversation-2",
            }
        },
    )

    assert "__interrupt__" not in result
    assert "Travora specializes" in result["final_answer"]
