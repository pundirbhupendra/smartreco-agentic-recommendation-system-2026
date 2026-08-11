"""Authentication service for user login, registration, and JWT handling."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.repositories.user_repository import UserRepository
from src.database.models.user import User

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password must be 72 bytes or fewer")
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            return False
        try:
            return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
        except ValueError:
            return False

    def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[int]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id: Optional[str] = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except (JWTError, ValueError):
            return None

    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Register a new user."""
        # Check if user already exists
        if self.user_repo.get_by_email(email) or self.user_repo.get_by_username(username):
            return None

        # Create new user
        try:
            hashed_password = self.hash_password(password)
        except ValueError:
            return None
        user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
        }
        return self.user_repo.create(user_data)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user and return user object if valid."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token."""
        user_id = self.verify_token(token)
        if user_id is None:
            return None
        return self.user_repo.get_by_id(user_id)
