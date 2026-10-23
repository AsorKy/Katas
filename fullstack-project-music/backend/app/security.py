from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

_hasher = PasswordHash.recommended() # Argon2


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None