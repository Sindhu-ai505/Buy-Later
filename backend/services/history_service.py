"""backend/services/history_service.py

Calculates user purchase history statistics and behavioral patterns.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import Purchase, WaitRecord, Feedback, Analysis


def get_user_history_stats(db: Session, user_id: int, current_category: str = "") -> Dict[str, Any]:
    """Calculates comprehensive purchase history and regret statistics for a user."""
    purchases: List[Purchase] = (
        db.query(Purchase).filter(Purchase.user_id == user_id).all()
    )

    total_purchases = len(purchases)
    total_spending = sum(p.price for p in purchases)
    avg_purchase_val = (total_spending / total_purchases) if total_purchases > 0 else 0.0

    now = datetime.utcnow()
    last_30_days = now - timedelta(days=30)
    last_90_days = now - timedelta(days=90)

    purchases_30d = [p for p in purchases if p.purchase_date >= last_30_days]
    purchases_90d = [p for p in purchases if p.purchase_date >= last_90_days]

    recent_spending_30d = sum(p.price for p in purchases_30d)

    # Days since last purchase
    if purchases:
        most_recent_date = max(p.purchase_date for p in purchases)
        days_since_last = max(0, (now - most_recent_date).days)
    else:
        days_since_last = 30  # Default reasonable baseline

    # Category counts & spending
    category_counts: Dict[str, int] = {}
    category_spending: Dict[str, float] = {}
    for p in purchases:
        cat = p.category or "General"
        category_counts[cat] = category_counts.get(cat, 0) + 1
        category_spending[cat] = category_spending.get(cat, 0.0) + p.price

    top_category = max(category_counts, key=category_counts.get) if category_counts else "None"
    current_cat_count = category_counts.get(current_category, 0) if current_category else 0
    current_cat_avg = (
        (category_spending.get(current_category, 0.0) / current_cat_count)
        if current_cat_count > 0
        else 0.0
    )

    # Regret rate calculation from purchases
    regret_purchases = [p for p in purchases if p.regret or (p.satisfaction in ["Regret", "Strong regret"])]
    regret_rate = (len(regret_purchases) / total_purchases) if total_purchases > 0 else 0.15

    # Purchases avoided from Wait records / Feedback
    user_analyses = db.query(Analysis).filter(Analysis.user_id == user_id).all()
    user_analysis_ids = [a.id for a in user_analyses]

    avoided_count = 0
    potential_savings = 0.0

    if user_analysis_ids:
        # Check wait records where decision was "Did not buy"
        wait_avoided = (
            db.query(WaitRecord)
            .filter(
                WaitRecord.analysis_id.in_(user_analysis_ids),
                WaitRecord.final_decision == "Did not buy",
            )
            .all()
        )
        avoided_ids = {w.analysis_id for w in wait_avoided}

        # Check feedbacks where purchased == False
        fb_avoided = (
            db.query(Feedback)
            .filter(
                Feedback.analysis_id.in_(user_analysis_ids),
                Feedback.purchased == False,
            )
            .all()
        )
        for fb in fb_avoided:
            avoided_ids.add(fb.analysis_id)

        avoided_count = len(avoided_ids)
        for a in user_analyses:
            if a.id in avoided_ids and a.product:
                potential_savings += a.product.price

    return {
        "total_purchases": total_purchases,
        "total_spending": round(total_spending, 2),
        "average_purchase_value": round(avg_purchase_val, 2),
        "purchases_30d_count": len(purchases_30d),
        "purchases_90d_count": len(purchases_90d),
        "recent_spending": round(recent_spending_30d, 2),
        "days_since_last_purchase": days_since_last,
        "category_counts": category_counts,
        "top_category": top_category,
        "category_purchase_count": current_cat_count,
        "average_category_spending": round(current_cat_avg, 2),
        "regret_rate": round(regret_rate, 3),
        "purchases_avoided": avoided_count,
        "potential_savings": round(potential_savings, 2),
    }
