from fastapi import APIRouter
from app.services.evaluation_service import get_action_stats

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/stats")
def get_stats():
    return get_action_stats()
