import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from arthmitra.backend.core.deps import get_current_user
from arthmitra.backend.database.session import get_db
from arthmitra.backend.database.models import FinancialProfile, User


router = APIRouter()


class UserProfileUpdate(BaseModel):
    # Financial profile fields are optional; we update only provided ones.
    emergency_fund: int | None = None
    total_investments: int | None = None
    monthly_sip: int | None = None
    term_cover: int | None = None
    health_cover: int | None = None
    epf_balance: int | None = None
    invested_80c: int | None = None
    has_nps: bool | None = None
    cc_outstanding: int | None = None
    equity_pct: float | None = None
    mhs_score: int | None = None
    mhs_dimensions: dict | None = None


@router.post("/api/users")
def create_user(db: Session = Depends(get_db)):
    """Deprecated: use POST /auth/signup. Kept for emergency dev fallback only."""
    raise HTTPException(
        status_code=410,
        detail="Anonymous user creation is disabled. Use POST /auth/signup instead.",
    )


@router.get("/api/users/{user_id}")
def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    try:
        uid = uuid.UUID(user_id)
        if current.id != uid:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        fp = db.query(FinancialProfile).filter(FinancialProfile.user_id == uid).first()
        if not fp:
            # Create an empty profile row so frontend can render consistently.
            fp = FinancialProfile(user_id=uid)
            db.add(fp)
            db.commit()
            db.refresh(fp)

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "age": user.age,
            "city": user.city,
            "is_salaried": user.is_salaried,
            "monthly_income": int(user.monthly_income),
            "monthly_expenses": int(user.monthly_expenses),
            "monthly_emi": int(user.monthly_emi),
            "risk_profile": user.risk_profile,
            "tax_regime": user.tax_regime,
            "financial_profile": {
                "emergency_fund": int(fp.emergency_fund),
                "total_investments": int(fp.total_investments),
                "monthly_sip": int(fp.monthly_sip),
                "term_cover": int(fp.term_cover),
                "health_cover": int(fp.health_cover),
                "epf_balance": int(fp.epf_balance),
                "invested_80c": int(fp.invested_80c),
                "has_nps": bool(fp.has_nps),
                "cc_outstanding": int(fp.cc_outstanding),
                "equity_pct": float(fp.equity_pct),
                "mhs_score": fp.mhs_score,
                "mhs_dimensions": fp.mhs_dimensions,
                "updated_at": fp.updated_at.isoformat() if fp.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.put("/api/users/{user_id}/profile")
def update_user_profile(
    user_id: str,
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    try:
        uid = uuid.UUID(user_id)
        if current.id != uid:
            raise HTTPException(status_code=403, detail="Forbidden")
        fp = db.query(FinancialProfile).filter(FinancialProfile.user_id == uid).first()
        if not fp:
            fp = FinancialProfile(user_id=uid)
            db.add(fp)

        update_data = body.dict(exclude_unset=True)
        for k, v in update_data.items():
            setattr(fp, k, v)

        db.commit()
        db.refresh(fp)

        return {
            "status": "ok",
            "financial_profile": {
                "emergency_fund": int(fp.emergency_fund),
                "total_investments": int(fp.total_investments),
                "monthly_sip": int(fp.monthly_sip),
                "term_cover": int(fp.term_cover),
                "health_cover": int(fp.health_cover),
                "epf_balance": int(fp.epf_balance),
                "invested_80c": int(fp.invested_80c),
                "has_nps": bool(fp.has_nps),
                "cc_outstanding": int(fp.cc_outstanding),
                "equity_pct": float(fp.equity_pct),
                "mhs_score": fp.mhs_score,
                "mhs_dimensions": fp.mhs_dimensions,
            },
        }
    except Exception as e:
        return {"error": str(e)}

