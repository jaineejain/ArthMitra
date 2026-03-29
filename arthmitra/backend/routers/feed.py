from fastapi import APIRouter
from ..services.arth_vaarta import get_arth_vaarta_content

router = APIRouter()

@router.get("/api/feed")
def get_feed():
    try:
        result = get_arth_vaarta_content()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}