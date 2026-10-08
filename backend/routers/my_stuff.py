"""backend/routers/my_stuff.py

API router for user inventory (My Stuff) management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import MyStuffCreate, MyStuffResponse
from backend.crud import (
    create_my_stuff,
    get_my_stuff_by_user,
    delete_my_stuff,
    get_my_stuff_item,
    get_user,
)

router = APIRouter(prefix="/my-stuff", tags=["My Stuff"])


@router.post("", response_model=MyStuffResponse, status_code=status.HTTP_201_CREATED)
def add_my_stuff(item: MyStuffCreate, db: Session = Depends(get_db)):
    user = get_user(db, item.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return create_my_stuff(db, item)


@router.get("/{user_id}", response_model=List[MyStuffResponse])
def list_user_stuff(user_id: int, db: Session = Depends(get_db)):
    return get_my_stuff_by_user(db, user_id)


@router.delete("/{item_id}")
def remove_my_stuff(item_id: int, db: Session = Depends(get_db)):
    success = delete_my_stuff(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return {"status": "success", "message": f"Item {item_id} deleted"}
