from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from pydantic_models.travel_request import TravelRequest


SYSTEM_PROMPT = """
You are the request-understanding component of an AI travel planner.

Your job is to convert the user's natural-language request into the
provided TravelRequest schema.

Capability rules:

FLIGHTS
Use FLIGHTS when:
- the user explicitly asks for flights, airfare, tickets, or air travel
- the user asks for a complete trip plan from an origin to a destination.

Examples:
- "Find flights from Athens to Tokyo."
- "Plan a trip to Japan from Greece."
- "Plan a 5 day trip to Japan from my city."


HOTELS
Use HOTELS when:
- the user explicitly asks for hotels, accommodation, lodging,
  or somewhere to stay;
- the user asks for a complete trip plan from an origin to a destination.

Examples:
- "Find hotels in Milan."
- "Where should I stay in Tokyo?"
- "Plan a trip to Japan from Greece."


ITINERARY
Use ITINERARY when the user asks to:
- plan a trip;
- create an itinerary;
- organize multiple travel days;
- create a daily schedule.

Examples:
- "Create a 5 day itinerary for Tokyo."
- "Plan a weekend in Rome."
- "Plan a 7 day trip to Japan from Greece."

Do not use ITINERARY when the user only asks for:
- flights;
- hotels;


ACTIVITIES
Use ACTIVITIES when the user explicitly asks for:
- sightseeing;
- attractions;
- things to do;
- experiences;
- tours;
- activities.

Examples:
- "What are the best things to do in Rome?"
- "Plan sightseeing activities in Kyoto."
- "Plan a trip to Japan including sightseeing."


Complete trip-planning rule:

- If the request includes ITINERARY and contains both an origin
  and a destination, treat it as an end-to-end trip request and
  include FLIGHTS, HOTELS, and ITINERARY.
- Add ACTIVITIES only if sightseeing or activities are explicitly requested.

Important rules:
- Do not add capabilities that are irrelevant to the request.
- A hotel-only request must not include FLIGHTS or ITINERARY.
- A flight-only request must not include HOTELS or ITINERARY.
- Never invent a user's departure location.
- If the user says something unresolved such as "my city",
  preserve that exact meaning in origin.
- Do not convert city or country names into airport codes.
  Location resolution is handled elsewhere by deterministic code.
- If information is not supplied, return null for that field.
- Extract only information that is explicitly stated or clearly implied
  by the user's request. Do not invent missing travel details.
"""


def understand_request(
    user_query: str,
    llm: BaseChatModel,
) -> TravelRequest:
    # Connects LLM output to the defined Pydantic schema parsing the user's request into a structured TravelRequest object.
    structured_llm = llm.with_structured_output(
        TravelRequest,
        method="json_schema",
    )

    result = structured_llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_query),
        ]
    )

    return result