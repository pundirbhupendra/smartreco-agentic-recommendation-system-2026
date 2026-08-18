"""Reusable FastAPI dependencies for database and authentication access."""

from typing import Annotated, Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models.user import User
from src.repositories.user_repository import UserRepository
from src.security import get_user_id_from_token


def _get_token(
    authorization: Optional[str],
    access_token: Optional[str],
) -> Optional[str]:
    """Prefer a Bearer header and fall back to the web-session cookie."""
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value:
            return value
    return access_token


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    access_token: Annotated[Optional[str], Cookie()] = None,
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer header or access cookie."""
    token = _get_token(authorization, access_token)
    user_id = get_user_id_from_token(token) if token else None
    user = UserRepository(db).get_by_id(user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Resolve the current admin using the project's current ID-1 rule."""
    if user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DatabaseSession = Annotated[Session, Depends(get_db)]
