"""backend/services/dashboard_service.py

Assembles dashboard metrics, spending analytics, and transparent AI behavioral insights.
Never presents insights as clinical psychological diagnoses.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import User, Analysis, Purchase
from backend.services.history_service import get_user_history_stats


def generate_ai_insights(history_stats: Dict[str, Any], analyses: List[Analysis]) -> List[str]:
    """Generates explainable spending insights derived strictly from logged data patterns."""
    insights = []

    total_analyses = len(analyses)
    if total_analyses == 0:
        return [
            "Welcome to BuyLater! As you evaluate purchases, personalized spending insights will appear here.",
            "Try adding items to 'My Stuff' to help the system detect duplicate purchases.",
        ]

    # Calculate impulse rates in analyzed items
    high_impulse_count = sum(1 for a in analyses if a.impulse_probability >= 0.50)
    high_impulse_pct = round((high_impulse_count / total_analyses) * 100, 1) if total_analyses else 0.0

    if high_impulse_pct >= 40.0:
        insights.append(
            f"Pattern Observed: {high_impulse_pct}% of your analyzed items flagged high impulse likelihood (frequently tied to promotions or sudden discovery)."
        )
    else:
        insights.append(
            f"Great discipline: Only {high_impulse_pct}% of your analyzed items showed elevated impulse indicators."
        )

    # Check potential savings
    savings = history_stats.get("potential_savings", 0.0)
    avoided = history_stats.get("purchases_avoided", 0)
    if avoided > 0:
        insights.append(
            f"Tangible Win: You avoided {avoided} non-essential purchases, preserving ₹{savings:,.2f} in your bank account."
        )

    # Category concentration
    top_cat = history_stats.get("top_category", "General")
    if top_cat != "None":
        insights.append(
            f"Category Focus: '{top_cat}' is your highest-spending category. Double-check utility before new purchases in this space."
        )

    # Regret rate note
    regret_rate = history_stats.get("regret_rate", 0.0)
    if regret_rate > 0.25:
        insights.append(
            f"Historical Feedback: {int(regret_rate * 100)}% of past logged purchases had reported regret. Taking a 7-day wait significantly cuts regret."
        )

    return insights


def get_user_dashboard(db: Session, user_id: int) -> Dict[str, Any]:
    """Retrieves full metrics overview, recent actions, and AI insights."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    history = get_user_history_stats(db, user_id)
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )

    recent_analyses = []
    for a in analyses[:5]:
        p = a.product
        recent_analyses.append({
            "id": a.id,
            "product_name": p.name if p else "Unknown",
            "category": p.category if p else "General",
            "price": p.price if p else 0.0,
            "purchase_score": a.purchase_score,
            "recommendation": a.recommendation,
            "impulse_probability": a.impulse_probability,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    purchases = (
        db.query(Purchase)
        .filter(Purchase.user_id == user_id)
        .order_by(Purchase.purchase_date.desc())
        .limit(5)
        .all()
    )

    recent_purchases = []
    for pur in purchases:
        p_name = pur.product.name if pur.product else f"Item #{pur.id}"
        recent_purchases.append({
            "id": pur.id,
            "product_name": p_name,
            "category": pur.category,
            "price": pur.price,
            "satisfaction": pur.satisfaction or "N/A",
            "regret": pur.regret,
            "purchase_date": pur.purchase_date.strftime("%Y-%m-%d"),
        })

    # Overall impulse rate across analyses
    impulse_analyses = [a for a in analyses if a.impulse_probability >= 0.50]
    impulse_rate = (
        round(len(impulse_analyses) / len(analyses), 2) if analyses else 0.0
    )

    ai_insights = generate_ai_insights(history, analyses)

    return {
        "user_id": user.id,
        "monthly_budget": user.monthly_budget,
        "total_spending": history["total_spending"],
        "total_purchases": history["total_purchases"],
        "average_purchase": history["average_purchase_value"],
        "impulse_rate": impulse_rate,
        "potential_savings": history["potential_savings"],
        "purchases_avoided": history["purchases_avoided"],
        "top_category": history["top_category"],
        "recent_analyses": recent_analyses,
        "recent_purchases": recent_purchases,
        "ai_insights": ai_insights,
    }
