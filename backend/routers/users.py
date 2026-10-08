"""backend/routers/users.py

API router for User management and personality customization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import UserCreate, UserResponse, PersonalityUpdate
from backend.crud import get_user, get_user_by_email, create_user, update_personality

router = APIRouter(prefix="", tags=["Users"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    return create_user(db, user)


@router.get("/users/{user_id}", response_model=UserResponse)
def fetch_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users/{user_id}/personality", response_model=UserResponse)
def set_user_personality(user_id: int, payload: PersonalityUpdate, db: Session = Depends(get_db)):
    user = update_personality(db, user_id, payload.personality)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users/{user_id}/personality")
def get_user_personality(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user_id": user.id, "personality": user.personality}
