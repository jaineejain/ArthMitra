import logging
import re
import hashlib
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from arthmitra.backend.core.deps import get_current_user
from arthmitra.backend.core.security import create_access_token, hash_password, verify_password
from arthmitra.backend.database.models import FinancialProfile, User
from arthmitra.backend.database.session import get_db

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")

# -------------------------------------------------------------------
# Password reset (token-based)
# Demo token store: kept in-memory.
# For production, use persistent storage + email delivery.
# -------------------------------------------------------------------

_RESET_TTL_SECONDS = 15 * 60  # 15 minutes
_RESET_TOKENS: dict[str, dict[str, Any]] = {}  # token_hash -> {user_id, expires_at}


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _norm_email(email: str) -> str:
    """Match signup storage: trim + lowercase so login finds the row."""
    return str(email).strip().lower()


class SignupBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError("Password must be at least 8 characters and include letters and numbers")
        return v


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    reset_token: str = Field(..., min_length=10, max_length=512)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError("Password must be at least 8 characters and include letters and numbers")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str | None


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db


@router.post("/auth/signup", response_model=TokenResponse)
def signup(body: SignupBody, db: Session | None = Depends(get_db)):
    db = _require_db(db)
    try:
        email_key = _norm_email(body.email)
        existing = (
            db.query(User)
            .filter(User.email.isnot(None), func.lower(func.trim(User.email)) == email_key)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            name=body.name.strip(),
            email=email_key,
            password_hash=hash_password(body.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        fp = FinancialProfile(user_id=user.id)
        db.add(fp)
        db.commit()

        token = create_access_token(str(user.id), {"email": user.email})
        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            email=user.email or "",
            name=user.name,
        )
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    except ProgrammingError as e:
        db.rollback()
        logger.exception("signup failed — DB schema issue: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database needs migration (e.g. email column). Stop the server, start it again so startup migrations run, then retry.",
        )
    except OperationalError as e:
        db.rollback()
        logger.exception("signup failed — DB connection: %s", e)
        err = str(e.orig) if getattr(e, "orig", None) else str(e)
        if "no password supplied" in err or "password authentication failed" in err.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "PostgreSQL rejected the connection (missing or wrong password). "
                    "Set DATABASE_URL in arthmitra/backend/.env (e.g. postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/arthmitra) "
                    "and restart the API."
                ),
            )
        raise HTTPException(
            status_code=503,
            detail="Cannot reach PostgreSQL. Check DATABASE_URL in arthmitra/backend/.env and that the server is running.",
        )
    except Exception as e:
        db.rollback()
        logger.exception("signup failed: %s", e)
        raise HTTPException(status_code=500, detail="Signup failed. Check API logs for details.")


@router.get("/auth/me")
def auth_me(current: User = Depends(get_current_user)):
    return {"user_id": str(current.id), "email": current.email or "", "name": current.name}


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginBody, db: Session | None = Depends(get_db)):
    db = _require_db(db)
    try:
        email_key = _norm_email(body.email)
        # Postgres UNIQUE(email) is case-sensitive, so legacy rows could duplicate the same address
        # with different casing; .first() would pick the wrong one. Try every normalized match.
        candidates = (
            db.query(User)
            .filter(User.email.isnot(None), func.lower(func.trim(User.email)) == email_key)
            .all()
        )
        user = next((u for u in candidates if verify_password(body.password, u.password_hash)), None)
        if not user:
            logger.info("Login rejected (unknown email or wrong password).")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(str(user.id), {"email": user.email})
        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            email=user.email or "",
            name=user.name,
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.exception("login failed — DB connection: %s", e)
        err = str(e.orig) if getattr(e, "orig", None) else str(e)
        if "no password supplied" in err or "password authentication failed" in err.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "PostgreSQL connection failed. Fix DATABASE_URL in arthmitra/backend/.env "
                    "(use 127.0.0.1 and include user:password) and restart the API."
                ),
            )
        raise HTTPException(status_code=503, detail="Cannot reach PostgreSQL. Check DATABASE_URL and that Postgres is running.")


@router.post("/auth/forgot-password")
def forgot_password(body: ForgotPasswordBody, db: Session | None = Depends(get_db)):
    """
    Request a password reset token (demo mode: in-memory token, no email delivery).
    Client will receive `reset_token` and must call /auth/reset-password immediately.
    """
    db = _require_db(db)

    email_key = _norm_email(body.email)
    user = (
        db.query(User)
        .filter(User.email.isnot(None), func.lower(func.trim(User.email)) == email_key)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(token)
    _RESET_TOKENS[token_hash] = {"user_id": str(user.id), "expires_at": time.time() + _RESET_TTL_SECONDS}

    return {"reset_token": token, "expires_in_seconds": _RESET_TTL_SECONDS}


@router.post("/auth/reset-password")
def reset_password(body: ResetPasswordBody, db: Session | None = Depends(get_db)):
    """
    Reset password using a reset token issued by /auth/forgot-password.
    Token is single-use and expires quickly.
    """
    db = _require_db(db)
    token_hash = _hash_reset_token(body.reset_token)

    entry = _RESET_TOKENS.get(token_hash)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if entry.get("expires_at", 0) < time.time():
        _RESET_TOKENS.pop(token_hash, None)
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = entry.get("user_id")
    if not user_id:
        _RESET_TOKENS.pop(token_hash, None)
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        _RESET_TOKENS.pop(token_hash, None)
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user.password_hash = hash_password(body.new_password)
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("reset password failed: %s", e)
        raise HTTPException(status_code=500, detail="Reset failed. Check API logs.")
    finally:
        # single-use token
        _RESET_TOKENS.pop(token_hash, None)

    return {"ok": True}
