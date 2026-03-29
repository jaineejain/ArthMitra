from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..services.bharat_score import calculate_bharat_score
from .chat import _extract_user_profile

router = APIRouter()

@router.get("/api/bharat-score")
def get_bharat_score(user_id: str = "demo-user", db: Session = Depends(get_db)):
    try:
        profile = _extract_user_profile(db, user_id)
        result = calculate_bharat_score(profile)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}