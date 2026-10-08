"""backend/routers/dashboard.py

API router for dashboard statistics and AI spending insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import DashboardResponse
from backend.services.dashboard_service import get_user_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{user_id}", response_model=DashboardResponse)
def fetch_dashboard(user_id: int, db: Session = Depends(get_db)):
    try:
        return get_user_dashboard(db, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
