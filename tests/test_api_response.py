import importlib
from datetime import date
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import ValidationError

from pydantic_models.api_response import ResponseType, TravelResponse
from pydantic_models.travel_request import RequestIntent, TravelCapability
from pydantic_models.trip_context import TripContextUpdate, TripTurn


THREAD_ID = "trip_" + "a" * 32


@pytest.mark.parametrize(
    ("status", "response_type", "brief"),
    [
        ("completed", "clarification", None),
        ("requires_input", "message", None),
        ("requires_confirmation", "trip_brief", None),
        ("completed", "message", {"destination": "Rome"}),
        ("cancelled", "travel_result", None),
        ("completed", None, None),
    ],
    ids=[
        "terminal_clarification",
        "pending_message",
        "missing_brief",
        "unexpected_brief",
        "cancelled_result",
        "missing_semantic_type",
    ],
)
def test_invalid_response_combinations(status, response_type, brief):
    with pytest.raises(ValidationError):
        TravelResponse(
            status=status,
            response_type=response_type,
            thread_id=THREAD_ID,
            answer="Reply",
            brief=brief,
        )


@pytest.fixture
def offline_app(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/travora")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_offline")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-offline")
    app_module = importlib.import_module("app")
    backend = importlib.import_module("backend")

    graph = backend.graph.compile(
        checkpointer=InMemorySaver(serde=backend.checkpoint_serializer)
    )
    monkeypatch.setattr(backend, "travel_graph", graph)
    # Verify HTTP transport without running the PostgreSQL startup lifespan.
    client = TestClient(app_module.app)
    try:
        yield client, backend, graph
    finally:
        client.close()


def test_travel_api_classifies_scope_interrupts_and_generated_result(
    offline_app, monkeypatch
):
    client, backend, graph = offline_app
    extract = Mock(
        side_effect=[
            TripTurn(intent=RequestIntent.OUT_OF_SCOPE, update=TripContextUpdate()),
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(
                    capabilities={TravelCapability.ITINERARY},
                    destination="Rome",
                ),
            ),
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(
                    duration_days=3,
                    dates_flexible=True,
                    travelers=2,
                ),
            ),
        ]
    )
    synthesize = Mock(return_value=AIMessage(content="A three-day Rome itinerary."))
    flights = Mock(side_effect=AssertionError("Flights were not requested."))
    search = Mock(side_effect=AssertionError("Web research was not requested."))
    monkeypatch.setattr("workflow.nodes.extract_trip_turn", extract)
    monkeypatch.setattr("workflow.nodes.search_flights_by_route", flights)
    monkeypatch.setattr("workflow.nodes.tavily_search", search)
    monkeypatch.setattr(type(backend.llm), "invoke", synthesize)

    scope_response = client.post(
        "/api/travel", json={"action": "start", "message": "Who invented Python?"}
    )
    assert scope_response.status_code == 200
    scope = scope_response.json()
    assert (scope["status"], scope["response_type"]) == ("completed", "message")
    assert scope["answer"].startswith("Travora specializes")
    assert scope["brief"] is None

    details_response = client.post(
        "/api/travel", json={"action": "start", "message": "Plan a trip to Rome."}
    )
    assert details_response.status_code == 200
    details = details_response.json()
    assert (details["status"], details["response_type"]) == (
        "requires_input", "clarification",
    )
    thread_id = details["thread_id"]
    assert thread_id != scope["thread_id"]

    wrong_phase = client.post(
        "/api/travel", json={"action": "build", "thread_id": thread_id}
    )
    assert wrong_phase.status_code == 409
    assert wrong_phase.json() == {
        "success": False,
        "error": "This trip is waiting for a different action.",
    }

    malformed = client.post(
        "/api/travel", json={"action": "build", "message": "yes", "thread_id": thread_id}
    )
    assert malformed.status_code == 422
    assert "detail" in malformed.json()
    assert extract.call_count == 2
    synthesize.assert_not_called()

    brief_response = client.post(
        "/api/travel",
        json={
            "action": "reply",
            "thread_id": thread_id,
            "message": "Three flexible days for two.",
        },
    )
    assert brief_response.status_code == 200
    brief = brief_response.json()
    assert (brief["status"], brief["response_type"]) == (
        "requires_confirmation", "trip_brief",
    )
    assert brief["thread_id"] == thread_id
    assert brief["brief"]["destination"] == "Rome"
    synthesize.assert_not_called()

    result_response = client.post(
        "/api/travel", json={"action": "build", "thread_id": thread_id}
    )
    assert result_response.status_code == 200
    assert result_response.json() == {
        "success": True,
        "status": "completed",
        "response_type": "travel_result",
        "thread_id": thread_id,
        "answer": "A three-day Rome itinerary.",
        "flight_results": "",
        "hotel_results": "",
        "activity_results": "",
        "itinerary": "",
        "brief": None,
    }
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    assert snapshot.values["terminal_response_type"] is ResponseType.TRAVEL_RESULT
    assert extract.call_count == 3
    synthesize.assert_called_once()
    flights.assert_not_called()
    search.assert_not_called()


def test_cancel_returns_message_and_closes_pending_session(offline_app, monkeypatch):
    client, _, _ = offline_app
    extract = Mock(
        return_value=TripTurn(
            intent=RequestIntent.TRAVEL,
            update=TripContextUpdate(capabilities={TravelCapability.ITINERARY}),
        )
    )
    monkeypatch.setattr("workflow.nodes.extract_trip_turn", extract)
    pending = client.post(
        "/api/travel", json={"action": "start", "message": "Help me plan a trip."}
    )
    assert pending.status_code == 200
    thread_id = pending.json()["thread_id"]

    cancelled = client.post(
        "/api/travel", json={"action": "cancel", "thread_id": thread_id}
    )
    assert cancelled.status_code == 200
    assert cancelled.json() == {
        "success": True,
        "status": "cancelled",
        "response_type": "message",
        "thread_id": thread_id,
        "answer": "Trip planning cancelled.",
        "flight_results": "",
        "hotel_results": "",
        "activity_results": "",
        "itinerary": "",
        "brief": None,
    }
    reply = client.post(
        "/api/travel", json={"action": "reply", "thread_id": thread_id, "message": "Rome"}
    )
    assert reply.status_code == 409
    extract.assert_called_once()


def test_greeting_is_chat_only_and_mixed_travel_uses_a_fresh_thread(
    offline_app, monkeypatch
):
    client, backend, graph = offline_app
    structured = Mock()
    structured.invoke.side_effect = [
        TripTurn(
            intent=RequestIntent.GREETING,
            update=TripContextUpdate(
                capabilities={TravelCapability.ITINERARY}, destination="Rome",
            ),
        ),
        TripTurn(
            intent=RequestIntent.TRAVEL,
            update=TripContextUpdate(
                capabilities={TravelCapability.ITINERARY}, destination="London",
            ),
        ),
    ]
    with_structured_output = Mock(return_value=structured)
    synthesize = Mock()
    flights = Mock()
    search = Mock()
    monkeypatch.setattr(type(backend.llm), "with_structured_output", with_structured_output)
    monkeypatch.setattr(type(backend.llm), "invoke", synthesize)
    monkeypatch.setattr("workflow.nodes.search_flights_by_route", flights)
    monkeypatch.setattr("workflow.nodes.tavily_search", search)

    response = client.post("/api/travel", json={"action": "start", "message": "Hi"})
    assert response.status_code == 200
    greeting = response.json()
    assert (greeting["status"], greeting["response_type"]) == ("completed", "message")
    assert greeting["answer"] == "Hi! I can help you plan a trip. Where would you like to go?"
    assert greeting["brief"] is None
    greeting_config = {"configurable": {"thread_id": greeting["thread_id"]}}
    greeting_state = graph.get_state(greeting_config).values
    assert greeting_state["parsed_request"].intent is RequestIntent.GREETING
    assert not greeting_state["parsed_request"].capabilities
    assert greeting_state["trip_context"].destination is None
    structured.invoke.assert_called_once()

    response = client.post(
        "/api/travel",
        json={"action": "start", "message": "Hi, plan a trip to London."},
    )
    assert response.status_code == 200
    travel = response.json()
    assert (travel["status"], travel["response_type"]) == (
        "requires_input", "clarification",
    )
    assert travel["thread_id"] != greeting["thread_id"]
    travel_config = {"configurable": {"thread_id": travel["thread_id"]}}
    assert graph.get_state(travel_config).values["trip_context"].destination == "London"
    assert structured.invoke.call_count == 2
    assert with_structured_output.call_count == 2
    synthesize.assert_not_called()
    flights.assert_not_called()
    search.assert_not_called()


def test_invalid_backend_response_keeps_generic_http_error(offline_app, monkeypatch):
    client, _, _ = offline_app
    result = {
        "status": "completed",
        "response_type": "clarification",
        "thread_id": THREAD_ID,
        "answer": "Invalid internal response.",
    }
    monkeypatch.setattr("app.run_travel_agent", Mock(return_value=result))

    response = client.post(
        "/api/travel", json={"action": "start", "message": "Plan a trip to Rome."}
    )

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": "An unexpected error occurred. Please try again.",
    }


@pytest.mark.parametrize(
    ("message", "intent"),
    [("Who invented Python?", RequestIntent.OUT_OF_SCOPE), ("Hi", RequestIntent.GREETING)],
    ids=["out_of_scope", "greeting"],
)
def test_unrelated_reply_repeats_the_question_without_reassessing_readiness(
    offline_app, monkeypatch, message, intent
):
    client, backend, graph = offline_app
    extract = Mock(
        side_effect=[
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(
                    capabilities={TravelCapability.ITINERARY},
                    destination="Rome",
                ),
            ),
            TripTurn(
                intent=intent,
                update=TripContextUpdate(destination="Paris"),
            ),
        ]
    )
    synthesize = Mock()
    flights = Mock()
    search = Mock()
    monkeypatch.setattr("workflow.nodes.extract_trip_turn", extract)
    monkeypatch.setattr(type(backend.llm), "invoke", synthesize)
    monkeypatch.setattr("workflow.nodes.search_flights_by_route", flights)
    monkeypatch.setattr("workflow.nodes.tavily_search", search)
    start = client.post(
        "/api/travel", json={"action": "start", "message": "Plan a trip to Rome."}
    ).json()
    thread_id = start["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}
    before = graph.get_state(config).values
    reassess = Mock(side_effect=AssertionError("Readiness must remain unchanged."))
    monkeypatch.setattr("workflow.nodes.assess_trip_readiness", reassess)

    response = client.post(
        "/api/travel",
        json={"action": "reply", "thread_id": thread_id, "message": message},
    )

    assert response.status_code == 200
    reply = response.json()
    assert (reply["status"], reply["response_type"]) == (
        "requires_input", "clarification",
    )
    assert reply["thread_id"] == thread_id
    assert reply["answer"].endswith(start["answer"])
    assert reply["answer"] != start["answer"]
    assert reply["brief"] is None
    after = graph.get_state(config).values
    for field in ("trip_context", "parsed_request", "trip_readiness", "user_query"):
        assert after[field] == before[field]
    assert after["messages"][-1].content == message
    assert extract.call_count == 2
    assert extract.call_args.kwargs["pending_question"] == start["answer"]
    reassess.assert_not_called()
    synthesize.assert_not_called()
    flights.assert_not_called()
    search.assert_not_called()


@pytest.mark.parametrize(
    ("message", "intent", "update"),
    [
        (
            "Who invented Python?",
            RequestIntent.OUT_OF_SCOPE,
            TripContextUpdate(destination="Paris"),
        ),
        ("Hi", RequestIntent.GREETING, TripContextUpdate()),
        ("yes", RequestIntent.UNCLEAR, TripContextUpdate()),
        ("yes", RequestIntent.TRAVEL, TripContextUpdate()),
        ("Keep Rome.", RequestIntent.TRAVEL, TripContextUpdate(destination="Rome")),
    ],
    ids=["out_of_scope", "greeting", "unclear_yes", "travel_yes", "same_trip_fact"],
)
def test_unchanged_edit_preserves_the_reviewed_request_for_explicit_build(
    offline_app, monkeypatch, message, intent, update
):
    client, backend, graph = offline_app
    original = "Plan three flexible days in Rome from Athens for two."
    extract = Mock(
        side_effect=[
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(
                    capabilities={TravelCapability.ITINERARY},
                    origin="Athens",
                    destination="Rome",
                    duration_days=3,
                    dates_flexible=True,
                    travelers=2,
                ),
            ),
            TripTurn(intent=intent, update=update),
        ]
    )
    synthesize = Mock(return_value=AIMessage(content="A three-day Rome itinerary."))
    flights = Mock(return_value="Flight research for Rome")
    search = Mock(return_value="Hotel research for Rome")
    monkeypatch.setattr("workflow.nodes.extract_trip_turn", extract)
    monkeypatch.setattr(type(backend.llm), "invoke", synthesize)
    monkeypatch.setattr("workflow.nodes.search_flights_by_route", flights)
    monkeypatch.setattr("workflow.nodes.tavily_search", search)
    initial = client.post("/api/travel", json={"action": "start", "message": original})
    assert initial.status_code == 200
    start = initial.json()
    assert start["response_type"] == "trip_brief"
    thread_id = start["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}
    before = graph.get_state(config).values

    response = client.post(
        "/api/travel", json={"action": "edit", "thread_id": thread_id, "message": message}
    )

    assert response.status_code == 200
    repeated = response.json()
    assert (repeated["status"], repeated["response_type"]) == (
        "requires_confirmation", "trip_brief",
    )
    assert repeated["thread_id"] == thread_id
    assert repeated["brief"] == start["brief"]
    assert "unchanged" in repeated["answer"]
    after = graph.get_state(config).values
    for field in ("trip_context", "parsed_request", "trip_readiness", "user_query"):
        assert after[field] == before[field]
    assert after["messages"][-1].content == message
    synthesize.assert_not_called()
    flights.assert_not_called()
    search.assert_not_called()

    built = client.post("/api/travel", json={"action": "build", "thread_id": thread_id})
    assert built.status_code == 200
    assert built.json()["response_type"] == "travel_result"
    assert extract.call_count == 2
    flights.assert_called_once_with(departure_iata="ATH", arrival_iata="FCO")
    search.assert_called_once_with("Best hotels in Rome")
    synthesize.assert_called_once()
    prompt = synthesize.call_args.args[0][-1].content
    assert f"Original user request:\n{original}" in prompt
    assert f"\n{message}\n" not in prompt
    assert before["parsed_request"].model_dump_json(exclude_none=True) in prompt


def test_material_edit_can_reopen_details_and_require_a_new_brief(
    offline_app, monkeypatch
):
    client, backend, _ = offline_app
    extract = Mock(
        side_effect=[
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(
                    capabilities={TravelCapability.ITINERARY},
                    destination="Rome",
                    duration_days=3,
                    dates_flexible=True,
                    travelers=2,
                ),
            ),
            TripTurn(
                intent=RequestIntent.UNCLEAR,
                update=TripContextUpdate(),
            ),
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(end_date=date(2099, 5, 3)),
            ),
            TripTurn(
                intent=RequestIntent.TRAVEL,
                update=TripContextUpdate(start_date=date(2099, 5, 1)),
            ),
        ]
    )
    synthesize = Mock()
    monkeypatch.setattr("workflow.nodes.extract_trip_turn", extract)
    monkeypatch.setattr(type(backend.llm), "invoke", synthesize)
    start = client.post(
        "/api/travel", json={"action": "start", "message": "Three flexible days in Rome for two."}
    )
    assert start.status_code == 200
    original_brief = start.json()["brief"]
    thread_id = start.json()["thread_id"]

    unchanged = client.post(
        "/api/travel",
        json={"action": "edit", "thread_id": thread_id, "message": "What?"},
    )
    assert unchanged.status_code == 200
    assert unchanged.json()["brief"] == original_brief

    edited = client.post(
        "/api/travel",
        json={"action": "edit", "thread_id": thread_id, "message": "Finish May 3, 2099."},
    )
    assert edited.status_code == 200
    assert edited.json()["response_type"] == "clarification"
    assert "start date" in edited.json()["answer"]
    assert client.post(
        "/api/travel", json={"action": "build", "thread_id": thread_id}
    ).status_code == 409

    reply = client.post(
        "/api/travel",
        json={"action": "reply", "thread_id": thread_id, "message": "Start May 1, 2099."},
    )
    assert reply.status_code == 200
    assert reply.json()["thread_id"] == thread_id
    assert reply.json()["response_type"] == "trip_brief"
    assert reply.json()["brief"]["travel_period"] != original_brief["travel_period"]
    assert reply.json()["brief"]["destination"] == "Rome"
    synthesize.assert_not_called()
