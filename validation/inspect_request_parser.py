import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from llm.request_parser import understand_request
from validation.request_check import check_request


load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)


TEST_PROMPTS = [
    "Give me budget hotel ideas in Milan under $120 per night.",

    "Find flights from Athens to Tokyo.",

    "Plan a 7 day trip to Japan from Greece including flights, hotels and sightseeing, under $3000.",

    "Plan a budget trip to Japan from my city.",

    "What are the best things to do in Rome?",

    "Find me hotels and flights for a trip from Athens to Paris.",
]


for prompt in TEST_PROMPTS:
    print("\n" + "=" * 80)
    print(f"PROMPT: {prompt}")

    parsed = understand_request(
        user_query=prompt,
        llm=llm,
    )

    print("PARSED REQUEST:")
    print(parsed.model_dump())

    check = check_request(parsed)
    print("REQUEST CHECK:")
    print(check.model_dump())