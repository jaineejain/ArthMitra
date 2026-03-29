from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..services.sapna_calculator import calculate_sapna_score
from .chat import _extract_user_profile

router = APIRouter()

@router.get("/api/sapna")
def get_sapna(user_id: str = "demo-user", db: Session = Depends(get_db)):
    try:
        profile = _extract_user_profile(db, user_id)
        result = calculate_sapna_score(profile)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}