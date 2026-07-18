"""Exposes MCP skills over plain HTTP as well, for clients that are not MCP-native."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.di import get_skill_registry

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillRunRequest(BaseModel):
    arguments: dict[str, Any] = {}


@router.get("")
async def list_skills() -> list[dict[str, str]]:
    return get_skill_registry().list_skills()


@router.post("/{skill_name}/run")
async def run_skill(skill_name: str, request: SkillRunRequest) -> Any:
    registry = get_skill_registry()
    if registry.get(skill_name) is None:
        raise HTTPException(status_code=404, detail=f"Unknown skill: {skill_name}")
    return await registry.run(skill_name, **request.arguments)
