import uuid

import os
import sys
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from arthmitra.backend.config import DATABASE_URL
from arthmitra.backend.database.session import SessionLocal, engine
from arthmitra.backend.database.models import FinancialProfile, User
from arthmitra.backend.services.finance_engine import calculate_mhs, calculate_karma_score


def _rupees_to_paise(v: int | float) -> int:
    return int(round(float(v) * 100.0))


def _get_or_create_user(db: Session, name: str, age: int, city: str, monthly_income_rupees: int) -> User:
    user = db.query(User).filter(User.name == name).first()
    if user:
        return user
    user = User(
        id=uuid.uuid4(),
        name=name,
        age=age,
        city=city,
        monthly_income=_rupees_to_paise(monthly_income_rupees),
        is_salaried=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_or_create_fp(db: Session, user: User) -> FinancialProfile:
    fp = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if fp:
        return fp
    fp = FinancialProfile(user_id=user.id)
    db.add(fp)
    db.commit()
    db.refresh(fp)
    return fp


def main():
    # If DB isn't initialized, fail silently.
    try:
        db = SessionLocal()
    except Exception:
        return

    try:
        users_count = db.query(User).count()
        if users_count and users_count > 0:
            return

        # Priya Sharma
        priya = _get_or_create_user(db, "Priya Sharma", 28, "Mumbai", 85000)
        priya.monthly_expenses = _rupees_to_paise(52000)
        priya.monthly_emi = _rupees_to_paise(18000)
        fp1 = _get_or_create_fp(db, priya)
        fp1.emergency_fund = _rupees_to_paise(45000)
        fp1.term_cover = 0
        fp1.health_cover = _rupees_to_paise(400000)
        fp1.monthly_sip = _rupees_to_paise(18000)
        fp1.total_investments = _rupees_to_paise(420000)
        fp1.invested_80c = _rupees_to_paise(92000)  # 80C gap ~ 58k from 1.5L cap
        fp1.has_nps = True
        fp1.cc_outstanding = 0
        fp1.equity_pct = 0.58

        mhs1 = calculate_mhs(
            {
                "age": priya.age,
                "is_salaried": priya.is_salaried,
                "monthly_income": priya.monthly_income,
                "monthly_expenses": priya.monthly_expenses,
                "monthly_emi": priya.monthly_emi,
                "emergency_fund": fp1.emergency_fund,
                "monthly_sip": fp1.monthly_sip,
                "term_cover": fp1.term_cover,
                "health_cover": fp1.health_cover,
                "cc_outstanding": fp1.cc_outstanding,
                "equity_pct": fp1.equity_pct,
                "invested_80c": fp1.invested_80c,
                "has_nps": fp1.has_nps,
                "total_investments": fp1.total_investments,
            }
        )
        fp1.mhs_score = mhs1["total"]
        fp1.mhs_dimensions = mhs1["dimensions"]
        fp1.updated_at = None

        # Arjun Mehta
        arjun = _get_or_create_user(db, "Arjun Mehta", 32, "Bangalore", 140000)
        arjun.monthly_expenses = _rupees_to_paise(78000)
        arjun.monthly_emi = _rupees_to_paise(22000)
        fp2 = _get_or_create_fp(db, arjun)
        fp2.emergency_fund = _rupees_to_paise(260000)
        fp2.term_cover = _rupees_to_paise(25000000)  # 2.5cr
        fp2.health_cover = _rupees_to_paise(700000)
        fp2.monthly_sip = _rupees_to_paise(15000)
        fp2.total_investments = _rupees_to_paise(950000)
        fp2.invested_80c = _rupees_to_paise(120000)
        fp2.has_nps = False
        fp2.cc_outstanding = 0
        fp2.equity_pct = 0.7

        mhs2 = calculate_mhs(
            {
                "age": arjun.age,
                "is_salaried": arjun.is_salaried,
                "monthly_income": arjun.monthly_income,
                "monthly_expenses": arjun.monthly_expenses,
                "monthly_emi": arjun.monthly_emi,
                "emergency_fund": fp2.emergency_fund,
                "monthly_sip": fp2.monthly_sip,
                "term_cover": fp2.term_cover,
                "health_cover": fp2.health_cover,
                "cc_outstanding": fp2.cc_outstanding,
                "equity_pct": fp2.equity_pct,
                "invested_80c": fp2.invested_80c,
                "has_nps": fp2.has_nps,
                "total_investments": fp2.total_investments,
            }
        )
        fp2.mhs_score = mhs2["total"]
        fp2.mhs_dimensions = mhs2["dimensions"]

        # Couple demo user as a single profile (used only for Dashboard widget demo)
        couple = _get_or_create_user(db, "Rahul Verma + Neha Verma", 30, "Delhi", 225000)
        couple.monthly_expenses = _rupees_to_paise(130000)
        couple.monthly_emi = _rupees_to_paise(20000)
        fp3 = _get_or_create_fp(db, couple)
        fp3.emergency_fund = _rupees_to_paise(380000)
        fp3.term_cover = _rupees_to_paise(12000000)
        fp3.health_cover = _rupees_to_paise(900000)
        fp3.monthly_sip = _rupees_to_paise(30000)
        fp3.total_investments = _rupees_to_paise(850000)
        fp3.invested_80c = _rupees_to_paise(150000)
        fp3.has_nps = True
        fp3.cc_outstanding = 0
        fp3.equity_pct = 0.68

        mhs3 = calculate_mhs(
            {
                "age": couple.age,
                "is_salaried": couple.is_salaried,
                "monthly_income": couple.monthly_income,
                "monthly_expenses": couple.monthly_expenses,
                "monthly_emi": couple.monthly_emi,
                "emergency_fund": fp3.emergency_fund,
                "monthly_sip": fp3.monthly_sip,
                "term_cover": fp3.term_cover,
                "health_cover": fp3.health_cover,
                "cc_outstanding": fp3.cc_outstanding,
                "equity_pct": fp3.equity_pct,
                "invested_80c": fp3.invested_80c,
                "has_nps": fp3.has_nps,
                "total_investments": fp3.total_investments,
            }
        )
        fp3.mhs_score = mhs3["total"]
        fp3.mhs_dimensions = mhs3["dimensions"]

        db.commit()
    except Exception:
        # Seed is demo-only; never hard-fail.
        pass
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

