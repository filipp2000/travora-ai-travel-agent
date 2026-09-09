import os  
import certifi
import pycountry
import airportsdata
import re
import requests
from dotenv import load_dotenv

from services.location_resolver import (
    find_location_mentions,
    resolve_location_to_iata,
)

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# Default origin when user says only destination, e.g. "Japan trip"
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "ATH")  # Default to Athens, Greece


BASE_URL = "https://api.aviationstack.com/v1/flights"



def parse_route(
    query: str,
) -> tuple[str | None, str | None]:
    """
    Legacy natural-language route parser.

    This remains temporarily so the existing
    application continues to work.

    In the new architecture, understand_request()
    will extract origin and destination, so this
    function will eventually be removed.
    """

    query = query.strip()
    query_lower = query.lower()

    global_keywords = [
        "all country",
        "all countries",
        "global flight",
        "global flights",
        "all flight",
        "all flights",
        "worldwide flight",
        "worldwide flights",
    ]

    if any(
        keyword in query_lower
        for keyword in global_keywords
    ):
        return None, None

    # Explicit IATA route:
    # ATH to NRT
    # ATH -> NRT
    iata_match = re.search(
        r"\b([A-Za-z]{3})\s*"
        r"(?:to|->|-)\s*"
        r"([A-Za-z]{3})\b",
        query,
    )

    if iata_match:
        departure = resolve_location_to_iata(
            iata_match.group(1)
        )

        arrival = resolve_location_to_iata(
            iata_match.group(2)
        )

        if departure and arrival:
            return departure, arrival

    # "from Greece to Japan"
    match = re.search(
        r"\bfrom\s+(.+?)\s+\bto\s+(.+?)"
        r"(?:\s+(?:on|for|under|including|with|in|at)\b"
        r"|[.!?]|$)",
        query_lower,
    )

    if match:
        origin_text = match.group(1)
        destination_text = match.group(2)

        return (
            resolve_location_to_iata(
                origin_text
            ),
            resolve_location_to_iata(
                destination_text
            ),
        )

    # "to Japan from Greece"
    match = re.search(
        r"\bto\s+(.+?)\s+\bfrom\s+(.+?)"
        r"(?:\s+(?:on|for|under|including|with|in|at)\b"
        r"|[.!?]|$)",
        query_lower,
    )

    if match:
        destination_text = match.group(1)
        origin_text = match.group(2)

        return (
            resolve_location_to_iata(
                origin_text
            ),
            resolve_location_to_iata(
                destination_text
            ),
        )

    mentions = find_location_mentions(query)

    # Example:
    # "Plan a Japan trip from Greece"
    match = re.search(
        r"\bfrom\s+(.+?)(?:[.!?]|$)",
        query_lower,
    )

    if match:
        origin_text = match.group(1)

        departure = resolve_location_to_iata(
            origin_text
        )
        
        for mention in mentions:
            candidate = resolve_location_to_iata(
                mention
            )

            if (
                candidate
                and candidate != departure
            ):
                return departure, candidate

        return departure, None

    # Example:
    # "flights to Tokyo"
    match = re.search(
        r"\bto\s+(.+?)(?:[.!?]|$)",
        query_lower,
    )

    if match:
        destination_text = match.group(1)

        arrival = resolve_location_to_iata(
            destination_text
        )

        return None, arrival

    # Two detected locations.
    if len(mentions) >= 2:
        departure = resolve_location_to_iata(
            mentions[0]
        )

        arrival = resolve_location_to_iata(
            mentions[1]
        )

        return departure, arrival

    # Destination-only request.
    if len(mentions) == 1:
        arrival = resolve_location_to_iata(
            mentions[0]
        )

        return DEFAULT_ORIGIN_IATA, arrival

    return None, None


def has_explicit_origin(
    query: str,
) -> bool:
    return bool(
        re.search(
            r"\bfrom\b",
            query.lower(),
        )
    )


def format_flight(
    flight: dict,
) -> str:
    airline = (
        flight
        .get("airline", {})
        .get("name")
        or "Unknown airline"
    )

    flight_number = (
        flight
        .get("flight", {})
        .get("iata")
        or "Unknown flight number"
    )

    status = (
        flight.get("flight_status")
        or "Unknown"
    )

    departure = (
        flight.get("departure", {})
        or {}
    )

    arrival = (
        flight.get("arrival", {})
        or {}
    )

    departure_airport = (
        departure.get("airport")
        or "Unknown departure airport"
    )

    departure_iata = (
        departure.get("iata")
        or "Unknown"
    )

    departure_terminal = (
        departure.get("terminal")
        or "N/A"
    )

    departure_gate = (
        departure.get("gate")
        or "N/A"
    )

    departure_scheduled = (
        departure.get("scheduled")
        or "Unknown"
    )

    departure_delay = departure.get("delay")

    departure_delay_text = (
        f"{departure_delay} minutes"
        if departure_delay is not None
        else "N/A"
    )

    arrival_airport = (
        arrival.get("airport")
        or "Unknown arrival airport"
    )

    arrival_iata = (
        arrival.get("iata")
        or "Unknown"
    )

    arrival_terminal = (
        arrival.get("terminal")
        or "N/A"
    )

    arrival_gate = (
        arrival.get("gate")
        or "N/A"
    )

    arrival_scheduled = (
        arrival.get("scheduled")
        or "Unknown"
    )

    arrival_delay = arrival.get("delay")

    arrival_delay_text = (
        f"{arrival_delay} minutes"
        if arrival_delay is not None
        else "N/A"
    )

    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {departure_airport}
- IATA: {departure_iata}
- Terminal: {departure_terminal}
- Gate: {departure_gate}
- Scheduled: {departure_scheduled}
- Delay: {departure_delay_text}

Arrival:
- Airport: {arrival_airport}
- IATA: {arrival_iata}
- Terminal: {arrival_terminal}
- Gate: {arrival_gate}
- Scheduled: {arrival_scheduled}
- Delay: {arrival_delay_text}
""".strip()


def search_flights(
    query: str,
    limit: int = 10,
) -> str:
    """
    Search AviationStack for live flight data.

    This function still accepts raw user text
    while Travora uses the legacy graph.
    """

    if not API_KEY:
        return (
            "Flight API error: "
            "AVIATIONSTACK_API_KEY is missing.\n"
            "Please add this in your .env file:\n"
            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )

    if limit < 1:
        return (
            "Flight search error: "
            "limit must be greater than zero."
        )

    limit = min(limit, 100)

    # Only once. Your current uploaded file
    # accidentally calls parse_route() twice.
    departure_iata, arrival_iata = parse_route(
        query
    )

    if (
        has_explicit_origin(query)
        and departure_iata is None
    ):
        return (
            "Flight search could not resolve "
            "the departure location. "
            "Please provide your departure city, "
            "country, airport, or IATA code."
        )

    params = {
        "access_key": API_KEY,
        "limit": limit,
    }

    if departure_iata:
        params["dep_iata"] = departure_iata

    if arrival_iata:
        params["arr_iata"] = arrival_iata

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as exc:
        return (
            f"Flight API request failed: {exc}"
        )

    except ValueError:
        return (
            "Flight API returned invalid JSON."
        )

    if "error" in data:
        error = data["error"]

        return (
            "Flight API error:\n"
            f"Code: "
            f"{error.get('code', 'Unknown')}\n"
            f"Message: "
            f"{error.get('message', 'Unknown error')}"
        )

    flight_data = data.get("data", [])

    if not flight_data:
        route_text = ""

        if departure_iata and arrival_iata:
            route_text = (
                f" for route "
                f"{departure_iata} "
                f"to {arrival_iata}"
            )

        elif departure_iata:
            route_text = (
                f" from {departure_iata}"
            )

        elif arrival_iata:
            route_text = (
                f" to {arrival_iata}"
            )

        return (
            f"No live flight data found"
            f"{route_text}.\n\n"
            "Note: AviationStack provides "
            "live/status flight data, "
            "not ticket prices."
        )

    if departure_iata and arrival_iata:
        route_info = (
            f"Live flights from "
            f"{departure_iata} "
            f"to {arrival_iata}"
        )

    elif departure_iata:
        route_info = (
            f"Live flights from "
            f"{departure_iata}"
        )

    elif arrival_iata:
        route_info = (
            f"Live flights to "
            f"{arrival_iata}"
        )

    else:
        route_info = "Global live flights"

    formatted_flights = [
        format_flight(flight)
        for flight in flight_data[:limit]
    ]

    return (
        f"{route_info}\n\n"
        + "\n\n---\n\n".join(
            formatted_flights
        )
    )


if __name__ == "__main__":
    print(
        search_flights(
            "Plan a 7 days Japan trip from Athens"
        )
    )

    print("\n" + "=" * 80 + "\n")

    print(
        search_flights(
            "all country flight info"
        )
    )