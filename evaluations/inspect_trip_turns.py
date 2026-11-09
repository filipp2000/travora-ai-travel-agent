import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from llm.request_parser import extract_trip_turn
from pydantic_models.travel_request import RequestIntent
from pydantic_models.trip_context import TripContext
from services.trip_context_service import merge_trip_context


load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

context = TripContext()

# Simulate two user messages in the same travel conversation.
turns = [
    (
        "Plan a 5-day trip to the Netherlands for €1200.",
        None,
    ),
    (
        "From Athens, traveling solo, in December 2026.",
        "Where are you departing from, when, and with how many people?",
    ),
]


for message, pending_question in turns:
    turn = extract_trip_turn(
        latest_message=message,
        current_context=context,
        pending_question=pending_question,
        llm=llm,
    )

    print("\nUSER:", message)
    print("INTENT:", turn.intent)
    print(
        "UPDATE:",
        turn.update.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
    )

    if turn.intent == RequestIntent.TRAVEL:
        # Only apply updates for accepted travel turns.
        context = merge_trip_context(context, turn.update)

    print(
        "CURRENT CONTEXT:",
        context.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
    )
