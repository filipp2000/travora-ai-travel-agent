from tavily import TavilyClient
import os
from dotenv import load_dotenv


load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def tavily_search(query):
    """
    Perform a search using the Tavily API.

    Args:
        query (str): The search query.

    Returns:
        str: Formatted search results from the Tavily API.
    """
    try:
        response = client.search(
            query=query,
            max_results=5,
        )
    except Exception as exc:
        return f"Tavily search failed: {exc}"

    results = response.get("results", [])

    if not results:
        return "No search results found."

    formatted_results = []

    for i, result in enumerate(results, start=1):
        title = result.get("title") or "Unknown"
        url = result.get("url") or ""
        snippet = (result.get("content") or "").strip()

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        formatted_results.append(
            f"{i}. **{title}**\n"
            f"   {url}\n"
            f"   {snippet}"
        )

    return "\n\n".join(formatted_results)