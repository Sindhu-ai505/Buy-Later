"""backend/services/feedback_service.py

Feedback Loop:
Collects post-decision satisfaction and purchase outcome.
If purchased: logs purchase history with satisfaction/regret.
If not purchased: records avoided purchase and accumulates savings.
Does NOT auto-retrain (exports available for offline learning).
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import Feedback, Purchase, Analysis, Product
from backend.schemas import FeedbackCreate, PurchaseCreate
from backend.crud import create_feedback, create_purchase, get_feedback_by_analysis, get_analysis


def submit_feedback(db: Session, feedback_in: FeedbackCreate) -> Dict[str, Any]:
    """Records feedback, creates purchase record if purchased, and logs regret."""
    analysis = get_analysis(db, feedback_in.analysis_id)
    if not analysis:
        raise ValueError(f"Analysis {feedback_in.analysis_id} not found")

    product: Product = analysis.product

    # Derive boolean regret
    is_regret = feedback_in.regret or (feedback_in.satisfaction in ["Regret", "Strong regret"])

    feedback_record = create_feedback(
        db,
        FeedbackCreate(
            analysis_id=feedback_in.analysis_id,
            purchased=feedback_in.purchased,
            satisfaction=feedback_in.satisfaction,
            regret=is_regret,
        ),
    )

    purchase_record = None
    if feedback_in.purchased:
        purchase_record = create_purchase(
            db,
            PurchaseCreate(
                user_id=analysis.user_id,
                product_id=product.id,
                price=product.price,
                category=product.category,
                satisfaction=feedback_in.satisfaction,
                used_frequency="Daily",
                regret=is_regret,
                purchase_date=datetime.utcnow(),
            ),
        )

    return {
        "feedback_id": feedback_record.id,
        "analysis_id": analysis.id,
        "purchased": feedback_in.purchased,
        "satisfaction": feedback_in.satisfaction,
        "regret": is_regret,
        "saved_amount": 0.0 if feedback_in.purchased else product.price,
        "purchase_id": purchase_record.id if purchase_record else None,
        "message": (
            "Purchase and satisfaction logged in your history."
            if feedback_in.purchased
            else f"Congratulations! You saved ₹{product.price:,.2f} by avoiding an impulse purchase."
        ),
    }
