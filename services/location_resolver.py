import re

import airportsdata
import pycountry


AIRPORTS = airportsdata.load("IATA")


COUNTRY_ALIASES = {
    "usa": "US",
    "u.s.a": "US",
    "u.s.": "US",
    "america": "US",
    "united states": "US",
    "uk": "GB",
    "u.k.": "GB",
    "britain": "GB",
    "england": "GB",
    "uae": "AE",
    "dubai": "AE",
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "vietnam": "VN",
    "bangladesh": "BD",
    "india": "IN",
    "japan": "JP",
    "china": "CN",
    "singapore": "SG",
    "malaysia": "MY",
    "thailand": "TH",
    "indonesia": "ID",
    "nepal": "NP",
    "qatar": "QA",
    "saudi arabia": "SA",
    "turkey": "TR",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "greece": "GR",
}


COUNTRY_MAIN_AIRPORT = {
    "BD": "DAC",
    "IN": "DEL",
    "JP": "NRT",
    "US": "JFK",
    "GB": "LHR",
    "AE": "DXB",
    "SG": "SIN",
    "MY": "KUL",
    "TH": "BKK",
    "ID": "CGK",
    "CN": "PEK",
    "KR": "ICN",
    "NP": "KTM",
    "QA": "DOH",
    "SA": "JED",
    "TR": "IST",
    "CA": "YYZ",
    "AU": "SYD",
    "DE": "FRA",
    "FR": "CDG",
    "IT": "FCO",
    "ES": "MAD",
    "GR": "ATH",
}


CITY_MAIN_AIRPORT = {
    "dhaka": "DAC",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "kolkata": "CCU",
    "chennai": "MAA",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",
    "new york": "JFK",
    "london": "LHR",
    "dubai": "DXB",
    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "bangkok": "BKK",
    "doha": "DOH",
    "istanbul": "IST",
    "toronto": "YYZ",
    "sydney": "SYD",
    "paris": "CDG",
    "rome": "FCO",
    "madrid": "MAD",
    "frankfurt": "FRA",
    "athens": "ATH",
}


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    stop_words = [
        "flight",
        "flights",
        "ticket",
        "tickets",
        "trip",
        "travel",
        "plan",
        "complete",
        "days",
        "day",
        "including",
        "hotel",
        "hotels",
        "sightseeing",
        "under",
        "budget",
        "info",
        "information",
    ]

    words = [
        word
        for word in text.split()
        if word not in stop_words
    ]

    return " ".join(words).strip()


def country_name_to_code(text: str) -> str | None:
    text = clean_text(text)

    if text in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text]

    try:
        country = pycountry.countries.lookup(text)
        return country.alpha_2
    except LookupError:
        pass

    for country in pycountry.countries:
        country_name = country.name.lower()

        if country_name in text:
            return country.alpha_2

    for alias, code in COUNTRY_ALIASES.items():
        if alias in text:
            return code

    return None


def airport_country_matches(
    airport: dict,
    country_code: str,
) -> bool:
    airport_country = (
        str(airport.get("country", ""))
        .upper()
        .strip()
    )

    if airport_country == country_code:
        return True

    country = pycountry.countries.get(
        alpha_2=country_code
    )

    if country:
        return (
            airport_country.lower()
            == country.name.lower()
        )

    return False


def get_best_airport_for_country(
    country_code: str,
) -> str | None:
    preferred = COUNTRY_MAIN_AIRPORT.get(
        country_code
    )

    if preferred and preferred in AIRPORTS:
        return preferred

    candidates: list[tuple[int, str]] = []

    for iata, airport in AIRPORTS.items():
        if not iata:
            continue

        if not airport_country_matches(
            airport,
            country_code,
        ):
            continue

        name = str(
            airport.get("name", "")
        ).lower()

        city = str(
            airport.get("city", "")
        ).lower()

        score = 0

        if "international" in name:
            score += 50

        if "intl" in name:
            score += 40

        if "capital" in name:
            score += 20

        if city:
            score += 5

        candidates.append((score, iata))

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]


def resolve_location_to_iata(
    location: str,
) -> str | None:
    """
    Resolve a city, country, airport name,
    or IATA code to an IATA airport code.

    Examples:
        Greece -> ATH
        Athens -> ATH
        Japan -> NRT
        Tokyo -> NRT
        NRT -> NRT
        my city -> None
    """

    if not location:
        return None

    raw_location = location.strip()

    # Already an IATA code.
    if re.fullmatch(
        r"[A-Za-z]{3}",
        raw_location,
    ):
        code = raw_location.upper()

        if code in AIRPORTS:
            return code

    location_clean = clean_text(raw_location)

    if not location_clean:
        return None

    # Known city mapping.
    if location_clean in CITY_MAIN_AIRPORT:
        return CITY_MAIN_AIRPORT[
            location_clean
        ]

    # Country-level location.
    country_code = country_name_to_code(
        location_clean
    )

    if country_code:
        airport = get_best_airport_for_country(
            country_code
        )

        if airport:
            return airport

    # Search the airport dataset for city/name matches.
    candidates: list[tuple[int, str]] = []

    for iata, airport in AIRPORTS.items():
        city = str(
            airport.get("city", "")
        ).lower().strip()

        name = str(
            airport.get("name", "")
        ).lower().strip()

        score = 0

        if city == location_clean:
            score += 100
        elif location_clean in city:
            score += 70

        if location_clean in name:
            score += 50

        # No actual location match -> this airport is irrelevant.
        if score == 0:
            continue

        # Only use "international" as a bonus after a real match.
        if "international" in name:
            score += 10

        candidates.append((score, iata))

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]


def find_location_mentions(
    query: str,
) -> list[str]:
    """
    Find known country/city mentions inside
    a natural-language query.

    This helper exists only for the legacy
    parse_route() implementation.
    """

    query_lower = query.lower()
    mentions: list[str] = []

    for alias in COUNTRY_ALIASES:
        if re.search(
            rf"\b{re.escape(alias)}\b",
            query_lower,
        ):
            mentions.append(alias)

    for country in pycountry.countries:
        name = country.name.lower()

        if (
            len(name) >= 4
            and re.search(
                rf"\b{re.escape(name)}\b",
                query_lower,
            )
        ):
            mentions.append(name)

    for city in CITY_MAIN_AIRPORT:
        if re.search(
            rf"\b{re.escape(city)}\b",
            query_lower,
        ):
            mentions.append(city)

    # Deduplicate while preserving order.
    return list(dict.fromkeys(mentions))