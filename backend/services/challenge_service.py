"""backend/services/challenge_service.py

Builds the strongest reasonable case FOR buying, constructed strictly from the user's real answers.
Crucial rule: Does NOT alter stored scores or recommendation.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import Analysis, Product, User
from backend.services.behavior_service import extract_behavior_features
from backend.utils.personality import get_personality_profile


def generate_challenge(db: Session, analysis_id: int) -> Dict[str, Any]:
    """Assembles affirmative arguments advocating for the purchase based on answers."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError("Analysis not found")

    product: Product = analysis.product
    user: User = analysis.user

    features = extract_behavior_features(db, user, product, analysis.id)
    ans = features.get("raw_answers", {})
    profile = get_personality_profile(user.personality)

    args_for_buying = []

    # Check broken item
    if ans.get("existing_condition") == "broken":
        args_for_buying.append(
            f"Your current item is non-functional; replacing it restores your daily productivity."
        )

    # Check daily usage
    if ans.get("usage_frequency") in ["daily", "weekly"]:
        args_for_buying.append(
            f"High regular usage ({ans.get('usage_frequency')}) ensures strong utility value per rupee spent over time."
        )

    # Check planning
    if ans.get("planned_status") == "planned":
        args_for_buying.append(
            "This was not an accidental discovery; you have spent meaningful time evaluating this need."
        )

    # Check discount
    if features.get("discount_present") == 1:
        args_for_buying.append(
            "Taking advantage of an active discount can save money compared to purchasing at regular MRP later."
        )

    # Check budget
    if features.get("price_to_budget_ratio", 0) <= 0.20:
        args_for_buying.append(
            f"At ₹{product.price:,.2f}, this fits safely within your ₹{user.monthly_budget:,.2f} monthly allowance without financial crisis."
        )

    # Fallback supportive argument if list is empty
    if not args_for_buying:
        args_for_buying.append(
            f"Investing in '{product.name}' offers convenience, modern capabilities, and high personal satisfaction."
        )

    challenge_intro = profile.get("challenge_intro", "Here are the strong points in favor of buying:")
    full_challenge_text = (
        f"{challenge_intro}\n\n"
        + "\n".join([f"✓ {arg}" for arg in args_for_buying])
    )

    return {
        "analysis_id": analysis.id,
        "challenge_title": f"The Devil's Advocate: Case FOR '{product.name}'",
        "challenge_text": full_challenge_text,
        "arguments_for_buying": args_for_buying,
    }
