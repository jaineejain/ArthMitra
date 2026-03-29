"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from arthmitra.backend.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET


def hash_password(password: str) -> str:
    """Bcrypt directly — avoids passlib + bcrypt 4.x compatibility issues."""
    pw = password.encode("utf-8")
    if len(pw) > 72:
        pw = pw[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str | bytes | None) -> bool:
    """Must apply the same 72-byte rule as hash_password; hash may be str or bytes from some drivers."""
    if not hashed:
        return False
    if isinstance(hashed, bytes):
        h = hashed.decode("utf-8").strip()
    else:
        h = str(hashed).strip()
    if not h:
        return False
    try:
        pw = plain.encode("utf-8")
        if len(pw) > 72:
            pw = pw[:72]
        return bcrypt.checkpw(pw, h.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
