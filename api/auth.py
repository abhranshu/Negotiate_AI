"""
JWT Authentication utilities.
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.cache import AUTH_USER_CACHE
from api.config import settings
from api.database import get_db
from api.models.user import User

# Use pbkdf2_sha256 for broad runtime compatibility (notably Python 3.13 on Windows).
pwd_context    = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _load_user(db: Session, user_id: str) -> Optional[User]:
    """Fetch a user row, served from a short-TTL process cache.

    Every authenticated request needs this row, and in the deployed setup the
    database is remote (Supabase pooler), so it costs a full network round-trip
    per request.

    Caching user data is only safe because nothing in this API writes to a user
    row after creation and no endpoint reads a user relationship. The TTL bounds
    how long a stale copy can survive, and any future write path must call
    invalidate_user_cache(). Set AUTH_USER_CACHE_TTL_SECONDS=0 to opt out.
    """
    ttl = settings.AUTH_USER_CACHE_TTL_SECONDS
    if ttl <= 0:
        return db.query(User).filter(User.id == user_id).first()

    cached = AUTH_USER_CACHE.get(user_id)
    if cached is not None:
        return cached

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None

    # Detach before caching so the instance is not left bound to this request's
    # session (get_db closes it). Every column is loaded eagerly and nothing
    # touches a user relationship, so attribute access stays valid afterwards.
    db.expunge(user)
    AUTH_USER_CACHE.set(user_id, user, ttl)
    return user


def invalidate_user_cache(user_id: str) -> None:
    """Drop a cached user row. Call from anywhere a user row is written."""
    AUTH_USER_CACHE.invalidate(user_id)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = _load_user(db, user_id)
    if user is None:
        raise credentials_exception
    return user
