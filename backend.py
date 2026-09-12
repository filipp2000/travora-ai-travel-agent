import os
import uuid
from functools import partial

import certifi
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from workflow.nodes import (
    activities_node,
    check_request_node,
    clarify_request_node,
    final_response_node,
    flight_node,
    hotel_node,
    itinerary_node,
    join_services_node,
    understand_request_node,
)
from workflow.routing import (
    route_after_check,
    route_after_research,
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
            "DATABASE_URL is missing. "
            "Please add it to your environment variables."
        )

    # Render PostgreSQL requires SSL for external connections.
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = (
            f"{database_url}{separator}sslmode=require"
        )

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Please add it to your environment variables."
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

# Convert the raw user prompt into our typed TravelRequest.
graph.add_node(
    "understand_request",
    partial(
        understand_request_node,
        llm=llm,
    ),
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
# Generation nodes
# ---------------------------------------------------------

graph.add_node(
    "itinerary_node",
    partial(
        itinerary_node,
        llm=llm,
    ),
)

graph.add_node(
    "final_response_node",
    partial(
        final_response_node,
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

graph.add_edge(
    "understand_request",
    "check_request",
)


# These are all valid destinations that route_after_check()
# may return.
REQUEST_ROUTES = [
    "clarify_request",
    "flight_node",
    "hotel_node",
    "activities_node",
    "itinerary_node",
    "final_response_node",
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
graph.add_conditional_edges(
    "clarify_request",
    route_after_check,
    REQUEST_ROUTES,
)


# ---------------------------------------------------------
# Parallel research fan-in
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
graph.add_conditional_edges(
    "join_services",
    route_after_research,
    [
        "itinerary_node",
        "final_response_node",
    ],
)


# Itinerary generation always flows into the final response.
graph.add_edge(
    "itinerary_node",
    "final_response_node",
)

graph.add_edge(
    "final_response_node",
    END,
)


# =========================================================
# PostgreSQL checkpointing
# =========================================================

DATABASE_URL = get_database_url()

# The checkpointer currently uses one persistent PostgreSQL
# connection. We will move DB lifecycle/pooling into the
# application lifespan during the concurrency/reliability phase.
_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row,
)

checkpointer = PostgresSaver(_conn)

# Creates LangGraph checkpoint tables if they do not exist.
# Later this should become an explicit deployment/startup
# migration rather than running on every module import.
checkpointer.setup()


travel_graph = graph.compile(
    checkpointer=checkpointer,
)


# =========================================================
# Graph execution helpers
# =========================================================

def _has_pending_interrupt(config: dict) -> bool:
    """
    Check whether the current thread is waiting for
    clarification from the user.
    """

    # Get the current state of the graph.
    snapshot = travel_graph.get_state(config)

    # Return True if bool(x) is True for any x in the iterable.
    return any(
        task.interrupts
        for task in snapshot.tasks
    )


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
    user_input: str,
    thread_id: str | None = None,
) -> dict:
    """
    Start a new planning session or resume a workflow
    that is waiting for clarification.

    Thread lifecycle:
    - Independent request -> new thread.
    - Clarification required -> keep the thread.
    - Clarification response -> resume the same thread.
    - Completed workflow -> thread is considered closed.
    """

    result: dict
    active_thread_id: str

    # -----------------------------------------------------
    # Resume only if this thread is actually interrupted.
    # -----------------------------------------------------
    if thread_id:
        resume_config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        if _has_pending_interrupt(
            resume_config
        ):
            active_thread_id = thread_id

            result = travel_graph.invoke(
                Command(
                    resume=user_input
                ),
                config=resume_config,
            )

        else:
            # The thread is completed, stale, or unknown.
            # Never reuse it for a new independent request.
            thread_id = None

    # -----------------------------------------------------
    # No resumable thread -> start a new planning session.
    # -----------------------------------------------------
    if not thread_id:
        active_thread_id = (
            f"trip_{uuid.uuid4().hex}"
        )

        config = {
            "configurable": {
                "thread_id":
                    active_thread_id,
            }
        }

        initial_state: TravelState = {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],
            "user_query": user_input,

            # Request understanding / validation
            "parsed_request": None,
            "request_check": None,

            # Service results are scoped to this trip.
            "flight_results": "",
            "hotel_results": "",
            "activity_results": "",

            # Generated outputs are also scoped
            # to this planning session.
            "itinerary": "",
            "final_answer": "",
        }

        result = travel_graph.invoke(
            initial_state,
            config=config,
        )

    # -----------------------------------------------------
    # The graph paused and needs user clarification.
    # -----------------------------------------------------
    clarification_question = (
        _get_interrupt_question(
            result
        )
    )

    if clarification_question:
        return {
            "status":
                "requires_input",

            # The frontend must preserve this ID
            # until the clarification is answered.
            "thread_id":
                active_thread_id,

            "answer":
                clarification_question,

            "flight_results":
                result.get(
                    "flight_results",
                    "",
                ),

            "hotel_results":
                result.get(
                    "hotel_results",
                    "",
                ),

            "activity_results":
                result.get(
                    "activity_results",
                    "",
                ),

            "itinerary":
                result.get(
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

        "flight_results":
            result.get(
                "flight_results",
                "",
            ),

        "hotel_results":
            result.get(
                "hotel_results",
                "",
            ),

        "activity_results":
            result.get(
                "activity_results",
                "",
            ),

        "itinerary":
            result.get(
                "itinerary",
                "",
            ),
    }