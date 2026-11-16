from fastapi import APIRouter

from app.services.ai_service import get_ai_status

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/status")
def ai_status():
    return get_ai_status()
