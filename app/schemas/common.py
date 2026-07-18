from __future__ import annotations

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str
    code: str = "internal_error"
