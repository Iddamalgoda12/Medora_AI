from tavily import AsyncTavilyClient
from app.config.settings import settings

client = AsyncTavilyClient(
    api_key=settings.TAVILY_API_KEY
)


async def search_doctors(
    specialty: str,
    location: str
):

    query = (
        f"{specialty} doctors "
        f"in {location} Sri Lanka"
    )

    response = await client.search(
        query=query,
        max_results=5
    )

    return response.get("results", [])