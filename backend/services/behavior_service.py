"""backend/services/behavior_service.py

Extracts and engineers behavioral and financial features for the Deep Learning Impulse Model.
Combines product details, user financial profile, inventory records (My Stuff),
historical transactions, and adaptive question responses.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import User, Product, QuestionAnswer
from backend.services.my_stuff_service import find_similar_owned_items
from backend.services.history_service import get_user_history_stats


def extract_behavior_features(
    db: Session, user: User, product: Product, analysis_id: int
) -> Dict[str, Any]:
    """Compiles all 17 features required by the Deep Learning impulse model."""
    answers = (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.analysis_id == analysis_id)
        .all()
    )
    ans_map = {qa.question: qa.answer for qa in answers}

    history = get_user_history_stats(db, user.id, product.category)
    similar_owned = find_similar_owned_items(db, user.id, product)

    # 1. Price
    price = float(product.price)

    # 2. Monthly Budget
    monthly_budget = float(user.monthly_budget or 20000.0)

    # 3. Price to budget ratio
    price_to_budget_ratio = round(price / (monthly_budget + 1e-5), 4)

    # 4. Similar item owned
    has_similar_db = len(similar_owned) > 0
    has_similar_ans = ans_map.get("similar_item") == "yes_similar" or "existing_condition" in ans_map
    similar_item_owned = 1 if (has_similar_db or has_similar_ans) else 0

    # 5. Existing item working
    cond_ans = ans_map.get("existing_condition", "")
    if cond_ans == "working_fine":
        existing_item_working = 1
    elif cond_ans == "broken":
        existing_item_working = 0
    elif similar_owned:
        existing_item_working = 1 if similar_owned[0]["condition"].lower() == "working" else 0
    else:
        existing_item_working = 0

    # 6. Planned purchase
    planned_status = ans_map.get("planned_status", "")
    planned_purchase = 1 if planned_status == "planned" else 0

    # 7. Expected usage (days per month)
    freq_map = {
        "daily": 30,
        "weekly": 12,
        "monthly": 3,
        "rarely": 1,
    }
    expected_usage = freq_map.get(ans_map.get("usage_frequency", ""), 4)

    # 8-12. History features
    recent_purchases = int(history.get("purchases_30d_count", 0))
    recent_spending = float(history.get("recent_spending", 0.0))
    average_purchase_value = float(history.get("average_purchase_value", 0.0))
    category_purchase_count = int(history.get("category_purchase_count", 0))
    days_since_last_purchase = int(history.get("days_since_last_purchase", 15))

    # 13. Discount present
    discount_present = 1 if (planned_status == "discount_saw" or ans_map.get("delay_7days") == "deal_expires") else 0

    # 14. Social media influence
    social_media_influence = 1 if planned_status == "social_ad" else 0

    # 15. Sale influence
    sale_influence = 1 if (planned_status == "discount_saw" or ans_map.get("delay_7days") == "deal_expires") else 0

    # 16. Purchase reason
    upgrade_ans = ans_map.get("upgrade_reason", "")
    if cond_ans == "broken":
        purchase_reason = "replacement"
    elif upgrade_ans == "essential_feature":
        purchase_reason = "genuine_need"
    elif upgrade_ans in ["minor_upgrade", "novelty"]:
        purchase_reason = "upgrade"
    elif planned_status == "discount_saw":
        purchase_reason = "discount"
    elif planned_status == "social_ad":
        purchase_reason = "social_media"
    elif planned_status == "browsing_impulse":
        purchase_reason = "looks_cool"
    elif planned_status == "planned":
        purchase_reason = "genuine_need"
    else:
        purchase_reason = "genuine_need"

    # 17. Previous regret rate
    previous_regret_rate = float(history.get("regret_rate", 0.15))

    return {
        "price": price,
        "monthly_budget": monthly_budget,
        "price_to_budget_ratio": price_to_budget_ratio,
        "similar_item_owned": similar_item_owned,
        "existing_item_working": existing_item_working,
        "planned_purchase": planned_purchase,
        "expected_usage": expected_usage,
        "recent_purchases": recent_purchases,
        "recent_spending": recent_spending,
        "average_purchase_value": average_purchase_value,
        "category_purchase_count": category_purchase_count,
        "days_since_last_purchase": days_since_last_purchase,
        "discount_present": discount_present,
        "social_media_influence": social_media_influence,
        "sale_influence": sale_influence,
        "purchase_reason": purchase_reason,
        "previous_regret_rate": previous_regret_rate,
        # Contextual metadata
        "raw_answers": ans_map,
        "similar_owned_items": similar_owned,
    }
