from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db

router = APIRouter()

@router.get("/api/goals")
def get_goals(db: Session = Depends(get_db)):
    try:
        # Placeholder for goals
        return {"success": True, "data": {"goals": [], "message": "Goals coming soon"}}
    except Exception as e:
        return {"success": False, "error": str(e)}