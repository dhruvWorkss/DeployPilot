from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class User:
    subject: str
    role: str


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
    settings = get_settings()
    if settings.auth_disabled:
        return User("local-operator", "admin")
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return User(str(payload["sub"]), str(payload.get("role", "viewer")))
    except (JWTError, KeyError) as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid access token") from error


def operator(user: User = Depends(current_user)) -> User:
    if user.role not in {"operator", "admin"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operator role required")
    return user
