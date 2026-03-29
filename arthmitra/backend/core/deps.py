"""FastAPI dependencies: auth + DB user resolution."""

import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from arthmitra.backend.core.security import decode_token
from arthmitra.backend.database.models import User
from arthmitra.backend.database.session import get_db

security = HTTPBearer(auto_error=False)


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db


def get_current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session | None = Depends(get_db),
) -> uuid.UUID:
    db = _require_db(db)
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(creds.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        return uuid.UUID(str(payload["sub"]))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")


def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session | None = Depends(get_db),
) -> User:
    db = _require_db(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
