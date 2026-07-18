"""
Skill contract and registry.

Each skill is a small, isolated unit of capability (search documents,
summarize, translate, run a calculation, etc). The MCP server exposes
every registered skill as an MCP tool; the LangGraph Tool Agent also reads
from the same registry, so there is exactly one place skills are defined
and two consumers (MCP clients and the internal agent graph).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Skill(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the skill and return a JSON-serializable result."""


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[dict[str, str]]:
        return [{"name": s.name, "description": s.description} for s in self._skills.values()]

    async def run(self, name: str, **kwargs: Any) -> Any:
        skill = self.get(name)
        if skill is None:
            raise KeyError(f"Unknown skill: {name}")
        return await skill.run(**kwargs)
