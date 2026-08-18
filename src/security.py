"""Shared JWT and password helpers.

New code should use these helpers instead of implementing authentication in a
route. Existing users created by the current AuthService use bcrypt; this
module intentionally uses PBKDF2-SHA256 for new authentication code.
"""

from datetime import datetime, timedelta, timezone
import os
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256."""
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain password against a PBKDF2-SHA256 hash."""
    return password_context.verify(password, password_hash)


def create_access_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create an HS256 JWT containing the user's ID."""
    lifetime = expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS)
    expires_at = datetime.now(timezone.utc) + lifetime
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_user_id_from_token(token: str) -> Optional[int]:
    """Return the user ID in a valid JWT, or None for an invalid token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        return int(subject) if subject is not None else None
    except (JWTError, TypeError, ValueError):
        return None
