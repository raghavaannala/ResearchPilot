import httpx
import logging
import asyncio

logger = logging.getLogger("semantic_scholar")

BASE_URL = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarClient:
    """Client for Semantic Scholar API (free, no key required)."""

    def __init__(self):
        self.rate_limit_delay = 1.0  # 100 requests per 5 minutes

    async def search_papers(self, query: str, limit: int = 10) -> list[dict]:
        """Search for papers by query string."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{BASE_URL}/paper/search",
                    params={
                        "query": query,
                        "limit": limit,
                        "fields": "title,authors,year,abstract,venue,url,citationCount,referenceCount",
                    },
                )
                response.raise_for_status()
                data = response.json()
                await asyncio.sleep(self.rate_limit_delay)
                return data.get("data", [])
            except Exception as e:
                logger.error(f"Semantic Scholar search error: {e}")
                return []

    async def get_paper(self, paper_id: str) -> dict:
        """Get a single paper by Semantic Scholar ID or DOI."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{BASE_URL}/paper/{paper_id}",
                    params={
                        "fields": "title,authors,year,abstract,venue,url,citationCount,references,citations",
                    },
                )
                response.raise_for_status()
                await asyncio.sleep(self.rate_limit_delay)
                return response.json()
            except Exception as e:
                logger.error(f"Semantic Scholar get paper error: {e}")
                return {}

    async def get_citations(self, paper_id: str, limit: int = 10) -> list[dict]:
        """Get papers that cite the given paper."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{BASE_URL}/paper/{paper_id}/citations",
                    params={
                        "limit": limit,
                        "fields": "title,authors,year,abstract,venue,url",
                    },
                )
                response.raise_for_status()
                await asyncio.sleep(self.rate_limit_delay)
                data = response.json()
                return [item.get("citingPaper", {}) for item in data.get("data", [])]
            except Exception as e:
                logger.error(f"Semantic Scholar citations error: {e}")
                return []
