"""backend/services/wait_service.py

Manages 7-day cooling-off wait records and re-evaluations.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import WaitRecord, Analysis
from backend.crud import create_wait_record, get_wait_record_by_analysis, update_wait_decision


def initiate_wait(db: Session, analysis_id: int, wait_days: int = 7) -> WaitRecord:
    """Creates or returns an active wait record for the specified analysis."""
    existing = get_wait_record_by_analysis(db, analysis_id)
    if existing:
        return existing
    return create_wait_record(db, analysis_id, wait_days)


def get_wait_status(db: Session, analysis_id: int) -> Dict[str, Any]:
    """Checks whether the cooling-off period has elapsed and returns status."""
    record = get_wait_record_by_analysis(db, analysis_id)
    if not record:
        return {"exists": False}

    now = datetime.utcnow()
    # Ready for recheck if current time is past recheck_date
    is_ready = now >= record.recheck_date or record.final_decision is not None

    return {
        "exists": True,
        "id": record.id,
        "analysis_id": record.analysis_id,
        "wait_days": record.wait_days,
        "start_date": record.start_date,
        "recheck_date": record.recheck_date,
        "final_decision": record.final_decision,
        "is_ready_for_recheck": is_ready,
        "days_elapsed": max(0, (now - record.start_date).days),
        "days_remaining": max(0, (record.recheck_date - now).days),
    }


def record_recheck_decision(db: Session, analysis_id: int, decision: str) -> WaitRecord:
    """
    Stores user's post-wait decision:
    'Bought', 'Did not buy', or 'Still deciding'.
    """
    record = update_wait_decision(db, analysis_id, decision)
    if not record:
        raise ValueError(f"No wait record found for analysis {analysis_id}")
    return record
