"""backend/routers/purchases.py

API router for user purchases and transaction history.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import PurchaseCreate, PurchaseResponse
from backend.crud import create_purchase, get_purchases_by_user, get_user

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.post("", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def record_purchase(purchase: PurchaseCreate, db: Session = Depends(get_db)):
    user = get_user(db, purchase.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return create_purchase(db, purchase)


@router.get("/{user_id}", response_model=List[PurchaseResponse])
def list_purchases(user_id: int, db: Session = Depends(get_db)):
    return get_purchases_by_user(db, user_id)
