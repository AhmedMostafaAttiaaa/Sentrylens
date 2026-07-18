"""
MCP server exposing every registered skill as an MCP tool.

Uses the official `mcp` Python SDK's FastMCP helper. Each skill's `run`
method is wrapped as a tool function with its docstring/description taken
from the skill definition, so adding a new skill to the registry
automatically makes it available to any MCP client (Claude Desktop,
Claude Code, or a custom agent) without touching this file.

Run with: python -m app.mcp.server
"""

from __future__ import annotations

import structlog

from app.core.di import get_skill_registry

logger = structlog.get_logger(__name__)


def build_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The 'mcp' package is not installed. Install it with `uv pip install mcp` "
            "to run the standalone MCP server."
        ) from exc

    registry = get_skill_registry()
    server = FastMCP("enterprise-vision-rag")

    for skill_info in registry.list_skills():
        skill_name = skill_info["name"]

        def _make_tool(name: str):
            async def _tool(**kwargs):
                return await registry.run(name, **kwargs)

            _tool.__name__ = name
            _tool.__doc__ = next(s["description"] for s in registry.list_skills() if s["name"] == name)
            return _tool

        server.add_tool(_make_tool(skill_name), name=skill_name)

    return server


if __name__ == "__main__":
    mcp_server = build_mcp_server()
    mcp_server.run()
