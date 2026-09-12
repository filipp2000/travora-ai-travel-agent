from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.types import interrupt

from llm.request_parser import understand_request
from pydantic_models.travel_request import TravelCapability
from tools.flight_tool import search_flights_by_route
from tools.tavily_tool import tavily_search
from validation.request_check import check_request
from workflow.state import TravelState
from services.request_policy import apply_request_policy


# Request understanding node
def understand_request_node(
    state: TravelState,
    *,
    llm: BaseChatModel,
) -> dict:
    # Step 1: Let the LLM extract semantic information
    # from the user's natural-language request.
    parsed_request = understand_request(
        user_query=state["user_query"],
        llm=llm,
    )

    # Step 2: Enforce deterministic Travora product rules
    # before validation and graph routing.
    normalized_request = apply_request_policy(
        parsed_request
    )

    return {
        "parsed_request": normalized_request,
    }

# Request validation node
def check_request_node(
    state: TravelState,
) -> dict:
    parsed_request = state["parsed_request"]

    if parsed_request is None:
        raise ValueError("Parsed request is missing.")

    result = check_request(parsed_request)

    return {
        "request_check": result,
    }
    

# Request clarification node with interruption
def clarify_request_node(
    state: TravelState,
) -> dict:
    parsed_request = state["parsed_request"]
    request_check = state["request_check"]

    if parsed_request is None or request_check is None:
        raise ValueError(
            "Request parsing/checking must happen before clarification."
        )

    error = request_check.errors[0]

    if error in {
        "missing_origin",
        "unresolved_origin",
    }:
        field = "origin"
        question = (
            "What city, country, or airport "
            "will you be departing from?"
        )

    elif error in {
        "missing_destination",
        "unresolved_destination",
    }:
        field = "destination"
        question = (
            "What city or country would you like to travel to?"
        )

    else:
        raise ValueError(
            f"Unsupported request validation error: {error}"
        )

    answer = interrupt(
        {
            "type": "clarification",
            "field": field,
            "question": question,
        }
    )
    
    # Update the parsed request with the clarified answer and re-check the request
    updated_request = parsed_request.model_copy(
        update={
            field: str(answer).strip(),
        }
    )

    updated_check = check_request(
        updated_request
    )

    return {
        "parsed_request": updated_request,
        "request_check": updated_check,
        "messages": [
            HumanMessage(content=str(answer))
        ],
    }
    

# Flight node
def flight_node(
    state: TravelState,
) -> dict:
    request_check = state["request_check"]

    if request_check is None:
        raise ValueError("Request check is missing.")

    flight_results = search_flights_by_route(
        departure_iata=request_check.origin_iata,
        arrival_iata=request_check.destination_iata,
    )

    return {
        "flight_results": flight_results,
    }
    

# Hotel node
def hotel_node(
    state: TravelState,
) -> dict:
    request = state["parsed_request"]

    if request is None:
        raise ValueError("Parsed request is missing.")

    query_parts = [
        f"Best hotels in {request.destination}"
    ]

    if (
        request.budget_amount is not None
        and request.budget_currency
    ):
        query_parts.append(
            f"under {request.budget_amount} "
            f"{request.budget_currency} per night"
        )

    if request.preferences:
        query_parts.append(
            "preferences: "
            + ", ".join(request.preferences)
        )

    hotel_results = tavily_search(
        ". ".join(query_parts)
    )

    return {
        "hotel_results": hotel_results,
    }
    

# Activities node using Tavily search (later can be replaced with a dedicated activities tools)
def activities_node(
    state: TravelState,
) -> dict:
    request = state["parsed_request"]

    if request is None:
        raise ValueError("Parsed request is missing.")

    query = (
        f"Best attractions, sightseeing and things to do "
        f"in {request.destination}"
    )

    activity_results = tavily_search(query)

    return {
        "activity_results": activity_results,
    }
    
    
# Join services node
def join_services_node(
    state: TravelState,
) -> dict:
    return {}


# Itinerary node
def itinerary_node(
    state: TravelState,
    *,
    llm: BaseChatModel,
) -> dict:
    request = state["parsed_request"]

    if request is None:
        raise ValueError("Parsed request is missing.")

    prompt = f"""
Create a practical travel itinerary.

Structured travel request:
{request.model_dump_json(indent=2)}

Flight information:
{state.get("flight_results", "")}

Hotel information:
{state.get("hotel_results", "")}

Activities and destination research:
{state.get("activity_results", "")}

Respect the user's duration, budget and preferences.
Do not invent live prices or availability.
"""

    response = llm.invoke(
        [
            SystemMessage(
                content="You are an expert travel planner."
            ),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "itinerary": response.content,
    }
    
    
# Final response node
def final_response_node(
    state: TravelState,
    *,
    llm: BaseChatModel,
) -> dict:
    request = state["parsed_request"]

    if request is None:
        raise ValueError("Parsed request is missing.")

    requested_capabilities = [
        capability.value
        for capability in request.capabilities
    ]

    prompt = f"""
Answer the user's travel request.

Original request:
{state["user_query"]}

Structured request:
{request.model_dump_json(indent=2)}

Requested capabilities:
{requested_capabilities}

Flight results:
{state.get("flight_results", "")}

Hotel results:
{state.get("hotel_results", "")}

Activities:
{state.get("activity_results", "")}

Itinerary:
{state.get("itinerary", "")}

Rules:
- Only include sections relevant to the user's requested capabilities.
- Do not include a flight section if flights were not requested.
- Do not include a hotel section if hotels were not requested.
- Do not fabricate live prices, availability, or provider data.
- Be concise and practical.
"""

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a professional travel planning assistant."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "final_answer": response.content,
        "messages": [response],
    }