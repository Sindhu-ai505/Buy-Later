"""backend/routers/feedback.py

API router for post-analysis user feedback (purchased, satisfaction, regret).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import FeedbackCreate, FeedbackResponse
from backend.crud import get_feedback_by_analysis
from backend.services.feedback_service import submit_feedback

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", status_code=status.HTTP_201_CREATED)
def record_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    try:
        res = submit_feedback(db, payload)
        return res
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/{analysis_id}", response_model=FeedbackResponse)
def get_feedback(analysis_id: int, db: Session = Depends(get_db)):
    feedback = get_feedback_by_analysis(db, analysis_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback recorded for this analysis",
        )
    return feedback
