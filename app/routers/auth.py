"""Minimal auth endpoint for issuing demo JWTs. Replace with a real user
store (Postgres-backed) before production use."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    username: str
    roles: list[str] = ["user"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def issue_token(request: TokenRequest) -> TokenResponse:
    token = create_access_token(subject=request.username, roles=request.roles)
    return TokenResponse(access_token=token)
