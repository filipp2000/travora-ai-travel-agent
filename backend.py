import os
import uuid
from functools import partial

import certifi
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from pydantic_models.api_request import SessionAction
from pydantic_models.travel_request import (
    RequestCheck,
    RequestIntent,
    TravelCapability,
    TravelRequest,
)
from pydantic_models.trip_context import BudgetScope, TripContext
from pydantic_models.trip_readiness import (
    ReadinessIssue,
    TripReadiness,
)
from services.session_lifecycle import (
    SessionConflictError,
    cancel_pending_session,
    require_pending_session,
)
from workflow.nodes import (
    activities_node,
    ask_trip_details_node,
    assess_trip_readiness_node,
    check_request_node,
    clarify_request_node,
    flight_node,
    generate_response_node,
    hotel_node,
    join_services_node,
    scope_response_node,
    understand_request_node,
)
from workflow.routing import (
    route_after_check,
    route_after_readiness,
    route_after_understanding,
)
from workflow.state import TravelState

# =========================================================
# Environment configuration
# =========================================================

load_dotenv()


# certificate configuration for the external HTTP clients in the application.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add it to your environment variables."
        )

    # Render PostgreSQL requires SSL for external connections.
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Please add it to your environment variables."
    )


# =========================================================
# LLM
# =========================================================

# Temperature 0 keeps request extraction and graph behavior
# more reproducible while we build the evaluation baseline.
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    temperature=0,
)


# =========================================================
# LangGraph definition
# =========================================================

graph = StateGraph(TravelState)


# ---------------------------------------------------------
# Request understanding
# ---------------------------------------------------------

graph.add_node(
    "scope_response",
    scope_response_node,
)

# Convert the raw user prompt into our typed TravelRequest.
graph.add_node(
    "understand_request",
    partial(
        understand_request_node,
        llm=llm,
    ),
)

# Determine whether the accumulated trip information is complete.
graph.add_node(
    "assess_trip_readiness",
    assess_trip_readiness_node,
)

# Ask for missing details and pause the current LangGraph thread.
graph.add_node(
    "ask_trip_details",
    ask_trip_details_node,
)

# Deterministically check whether the parsed request has
# enough valid information to execute the requested services.
graph.add_node(
    "check_request",
    check_request_node,
)

# Interrupt the graph when required information is missing
# or cannot be resolved.
graph.add_node(
    "clarify_request",
    clarify_request_node,
)


# ---------------------------------------------------------
# External service nodes
# ---------------------------------------------------------

graph.add_node(
    "flight_node",
    flight_node,
)

graph.add_node(
    "hotel_node",
    hotel_node,
)

graph.add_node(
    "activities_node",
    activities_node,
)


# ---------------------------------------------------------
# Research synchronization
# ---------------------------------------------------------

# The requested services may run in parallel.
#
# defer=True ensures this node runs once after every selected
# research branch has completed, even when only a subset of
# flight/hotel/activity nodes was selected dynamically.
graph.add_node(
    "join_services",
    join_services_node,
    defer=True,
)


# ---------------------------------------------------------
# Response node
# ---------------------------------------------------------

graph.add_node(
    "generate_response_node",
    partial(
        generate_response_node,
        llm=llm,
    ),
)

# =========================================================
# Graph edges
# =========================================================

# Every request is first understood and validated.
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

# Decide whether to ask for information or continue execution.
graph.add_conditional_edges(
    "assess_trip_readiness",
    route_after_readiness,
    [
        "ask_trip_details",
        "check_request",
    ],
)

# After receiving a clarification, interpret the user's reply
# using the accumulated context from the same LangGraph thread.
graph.add_edge(
    "ask_trip_details",
    "understand_request",
)

# These are all valid destinations that route_after_check()
# may return.
REQUEST_ROUTES = [
    "clarify_request",
    "scope_response",
    "flight_node",
    "hotel_node",
    "activities_node",
    "generate_response_node",
]


# ---------------------------------------------------------
# Conditional routing after validation
# ---------------------------------------------------------

graph.add_conditional_edges(
    "check_request",
    route_after_check,
    REQUEST_ROUTES,
)


# After clarification is supplied and validated again,
# route into the appropriate capability nodes.
graph.add_edge(
    "clarify_request",
    "check_request",
)


# ---------------------------------------------------------
# Parallel research
# ---------------------------------------------------------

# Any selected retrieval node eventually synchronizes
# through join_services.
graph.add_edge(
    "flight_node",
    "join_services",
)

graph.add_edge(
    "hotel_node",
    "join_services",
)

graph.add_edge(
    "activities_node",
    "join_services",
)


# Once research is complete, decide whether an itinerary
# still needs to be generated.
graph.add_edge(
    "join_services",
    "generate_response_node",
)


# Final response generation.
graph.add_edge(
    "generate_response_node",
    END,
)

graph.add_edge(
    "scope_response",
    END,
)

# =========================================================
# PostgreSQL checkpointing
# =========================================================

DATABASE_URL = get_database_url()

# Use a connection pool instead of a single persistent DB connection.
# This is important when using serverless PostgreSQL (like Neon).
db_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=0,
    max_size=4,
    timeout=30.0,
    max_idle=60.0,
    max_lifetime=900.0,
    kwargs={
        "autocommit": True,
        "row_factory": dict_row,
    },
    # Simple check to verify that a connection is still working.
    # Return quietly if the connection is still working, otherwise raise an exception.
    check=ConnectionPool.check_connection,
    open=False,
)

# Explicitly allow only our trusted domain models and enums
# to be reconstructed from persisted LangGraph checkpoints.
checkpoint_serializer = JsonPlusSerializer(
    allowed_msgpack_modules=[
        RequestIntent,
        TravelCapability,
        TravelRequest,
        RequestCheck,
        BudgetScope,
        TripContext,
        ReadinessIssue,
        TripReadiness,
    ],
    # Never fall back to Python pickle deserialization.
    pickle_fallback=False,
)

# Keep the existing Neon connection pool and checkpointing.
checkpointer = PostgresSaver(
    db_pool,
    serde=checkpoint_serializer,
)

travel_graph = graph.compile(
    checkpointer=checkpointer,
)


# =========================================================
# Graph execution helpers
# =========================================================


def _get_interrupt_question(
    result: dict,
) -> str | None:
    """
    Extract the clarification question returned by
    LangGraph's interrupt() mechanism.
    """

    interrupts = result.get("__interrupt__", ())

    if not interrupts:
        return None

    interrupt_value = getattr(
        interrupts[0],
        "value",
        interrupts[0],
    )

    if isinstance(interrupt_value, dict):
        return interrupt_value.get("question")

    return str(interrupt_value)


# =========================================================
# Public entry point used by FastAPI
# =========================================================


def run_travel_agent(
    user_input: str | None = None,
    thread_id: str | None = None,
    *,
    action: SessionAction,
) -> dict:
    """
    Execute an explicit session action.

    START  -> always create a new LangGraph thread.
    REPLY  -> resume only an interrupted, active thread.
    CANCEL -> persist cancellation without executing research.
    """

    # --------------------------------------------------
    # 1. Cancel existing planning session
    # --------------------------------------------------
    if action == SessionAction.CANCEL:
        if thread_id is None:
            raise ValueError("Cancel requires a thread_id.")

        # Persist cancellation without running any graph nodes.
        cancel_pending_session(
            travel_graph,
            thread_id,
        )

        return {
            "status": "cancelled",
            "thread_id": thread_id,
            "answer": "Trip planning cancelled.",
        }

    # --------------------------------------------------
    # 2. Resume an existing clarification
    # --------------------------------------------------
    if action == SessionAction.REPLY:
        if thread_id is None or user_input is None:
            raise ValueError("Reply requires message and thread_id.")

        # A stale, completed or cancelled thread raises 409
        # through SessionConflictError at the API boundary.
        config = require_pending_session(
            travel_graph,
            thread_id,
        )

        active_thread_id = thread_id

        result = travel_graph.invoke(
            Command(resume=user_input),
            config=config,
        )

    # --------------------------------------------------
    # 3. Start a completely independent trip
    # --------------------------------------------------
    elif action == SessionAction.START:
        if user_input is None or thread_id is not None:
            raise ValueError("Invalid new trip request.")
        
        # Each new trip gets an independent checkpoint thread.
        active_thread_id = f"trip_{uuid.uuid4().hex}"

        config = {
            "configurable": {
                "thread_id": active_thread_id,
            }
        }

        # Initialize all state required by the current workflow.
        initial_state: TravelState = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            
            # Conversational trip context
            "trip_context": TripContext(),
            
            # Readiness and clarification
            "trip_readiness": None,
            "pending_question": None,
            
            # Session lifecycle
            "session_cancelled": False,
            
            # Existing execution request and validation.
            "parsed_request": None,
            "request_check": None,
            
            # Results from external travel services.
            "flight_results": "",
            "hotel_results": "",
            "activity_results": "",
            
            # Generated outputs.
            "itinerary": "",
            "final_answer": "",
        }

        result = travel_graph.invoke(
            initial_state,
            config=config,
        )

    else:
        raise ValueError(f"Unsupported session action: {action}")

    # -----------------------------------------------------
    # The graph paused and needs user clarification.
    # -----------------------------------------------------
    clarification_question = _get_interrupt_question(result)

    if clarification_question:
        return {
            "status": "requires_input",
            # The frontend must preserve this ID
            # until the clarification is answered.
            "thread_id": active_thread_id,
            "answer": clarification_question,
            "flight_results": result.get(
                "flight_results",
                "",
            ),
            "hotel_results": result.get(
                "hotel_results",
                "",
            ),
            "activity_results": result.get(
                "activity_results",
                "",
            ),
            "itinerary": result.get(
                "itinerary",
                "",
            ),
        }

    # -----------------------------------------------------
    # Workflow finished. The thread remains persisted in
    # PostgreSQL but is considered closed by the product.
    # -----------------------------------------------------
    return {
        "status": "completed",
        "thread_id": active_thread_id,
        "answer": result.get(
            "final_answer",
            "",
        ),
        "flight_results": result.get(
            "flight_results",
            "",
        ),
        "hotel_results": result.get(
            "hotel_results",
            "",
        ),
        "activity_results": result.get(
            "activity_results",
            "",
        ),
        "itinerary": result.get(
            "itinerary",
            "",
        ),
    }
