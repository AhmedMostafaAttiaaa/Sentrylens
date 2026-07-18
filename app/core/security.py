"""JWT authentication and simple role based access control."""

from __future__ import annotations

import time
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(dict):
    @property
    def subject(self) -> str:
        return self.get("sub", "")

    @property
    def roles(self) -> list[str]:
        return self.get("roles", [])


def create_access_token(subject: str, roles: list[str], settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = int(time.time())
    payload = {
        "sub": subject,
        "roles": roles,
        "iat": now,
        "exp": now + settings.security.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.security.jwt_secret_key, algorithm=settings.security.jwt_algorithm)


def decode_access_token(token: str, settings: Settings | None = None) -> TokenPayload:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(token, settings.security.jwt_secret_key, algorithms=[settings.security.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    return TokenPayload(payload)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return decode_access_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    async def _checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if allowed_roles and not set(user.roles) & set(allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return _checker
