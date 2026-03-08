from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/protected")
def protected(user: User = Depends(get_current_user)):
    return {
        "message": "Auth works",
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }
