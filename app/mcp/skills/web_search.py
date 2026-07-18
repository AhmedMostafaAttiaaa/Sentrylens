"""
Web Search skill.

Isolated adapter around a configurable external search API. No provider
is bundled by default (to avoid shipping a hardcoded dependency on one
paid vendor); set WEB_SEARCH_API_URL and WEB_SEARCH_API_KEY and implement
_call_provider to point at your provider of choice (Tavily, Brave Search,
SerpAPI, etc). Raises clearly if not configured rather than silently
returning empty results.
"""

from __future__ import annotations

import os

import httpx

from app.mcp.skills.base import Skill


class WebSearchSkill(Skill):
    name = "web_search"
    description = "Search the public web for current information."

    async def run(self, query: str, max_results: int = 5) -> list[dict]:
        api_url = os.environ.get("WEB_SEARCH_API_URL")
        api_key = os.environ.get("WEB_SEARCH_API_KEY")
        if not api_url or not api_key:
            raise RuntimeError(
                "Web search is not configured. Set WEB_SEARCH_API_URL and "
                "WEB_SEARCH_API_KEY environment variables to enable this skill."
            )
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                api_url, params={"q": query, "limit": max_results}, headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            return response.json().get("results", [])
