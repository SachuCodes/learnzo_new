from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.auth.auth import verify_password, get_hashed_password, create_access_token
from app.models.learner import Learner

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_hashed_password(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed_password,
        role=payload.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if payload.role == "student":
        learner = Learner(user_id=user.id, name=None, age=None)
        db.add(learner)
        db.commit()

    return {"message": "User registered successfully", "role": payload.role}



@router.post("/login", response_model=Token)
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

   
    access_token = create_access_token({
        "user_id": user.id,
        "sub": user.email,
        "role": user.role
    })
    learner = user.learner
    has_learner = (
        learner is not None
        and learner.name is not None
        and learner.age is not None
        and learner.disability_type is not None
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        has_learner=has_learner
    )


# 🔥 DEBUG ENDPOINT — REMOVE AFTER CONFIRMATION
@router.get("/__ping")
def auth_ping():
    return {"auth": "alive"}
