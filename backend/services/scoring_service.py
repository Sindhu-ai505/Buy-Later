"""backend/services/scoring_service.py

Explainable Purchase Scoring Engine and Recommendation System.
Weights are centralized in one configuration dictionary.
Calculates factor scores (Need, Usage, Budget, Existing Product, Purchase Intent, Behavior)
and applies Deep Learning Impulse Probability dampening.
"""

from typing import Dict, Any, List, Tuple

# Centralized Weights Config Dict
SCORING_WEIGHTS = {
    "need": 0.25,
    "usage": 0.15,
    "budget": 0.20,
    "existing_product": 0.15,
    "purchase_intent": 0.15,
    "behavior": 0.10,
}


def calculate_need_score(features: Dict[str, Any]) -> float:
    """Calculates need score (0-100) based on condition of existing items and necessity."""
    ans = features.get("raw_answers", {})
    cond = ans.get("existing_condition", "")
    impact = ans.get("broken_impact", "")
    upgrade = ans.get("upgrade_reason", "")
    planned = ans.get("planned_status", "")

    if cond == "broken":
        if impact == "critical":
            return 95.0
        elif impact == "manageable":
            return 80.0
        return 70.0

    if features.get("similar_item_owned") == 1:
        if cond == "working_fine":
            if upgrade == "essential_feature":
                return 55.0
            elif upgrade == "minor_upgrade":
                return 30.0
            return 15.0  # Novelty
        elif cond == "minor_issues":
            return 50.0

    # No similar item owned
    if planned == "planned":
        return 75.0
    elif planned in ["discount_saw", "social_ad"]:
        return 40.0
    elif planned == "browsing_impulse":
        return 25.0

    return 50.0


def calculate_usage_score(features: Dict[str, Any]) -> float:
    """Calculates usage score (0-100) based on projected frequency."""
    ans = features.get("raw_answers", {})
    freq = ans.get("usage_frequency", "")

    if freq == "daily":
        return 95.0
    elif freq == "weekly":
        return 75.0
    elif freq == "monthly":
        return 40.0
    elif freq == "rarely":
        return 15.0

    # Fallback to numeric expected_usage days
    days = features.get("expected_usage", 4)
    if days >= 25:
        return 95.0
    elif days >= 10:
        return 75.0
    elif days >= 3:
        return 40.0
    return 15.0


def calculate_budget_score(features: Dict[str, Any]) -> float:
    """Calculates budget score (0-100) based on price-to-budget ratio and self-reported comfort."""
    ratio = features.get("price_to_budget_ratio", 0.1)
    ans = features.get("raw_answers", {})
    feeling = ans.get("budget_feeling", "")

    if ratio <= 0.05:
        base = 95.0
    elif ratio <= 0.15:
        base = 80.0
    elif ratio <= 0.30:
        base = 60.0
    elif ratio <= 0.50:
        base = 40.0
    else:
        base = 15.0

    # User self-assessment modifier
    if feeling == "comfortable":
        base = min(100.0, base + 5.0)
    elif feeling == "stretched":
        base = max(0.0, base - 15.0)

    return round(base, 1)


def calculate_existing_product_score(features: Dict[str, Any]) -> float:
    """Calculates existing product score (0-100). Higher means less redundant waste."""
    similar_owned = features.get("similar_item_owned", 0)
    ans = features.get("raw_answers", {})
    cond = ans.get("existing_condition", "")

    if not similar_owned:
        return 85.0

    if cond == "broken":
        return 90.0  # Replacement is warranted
    elif cond == "minor_issues":
        return 50.0
    elif cond == "working_fine":
        return 15.0  # Already has a working product

    return 40.0


def calculate_purchase_intent_score(features: Dict[str, Any], impulse_prob: float) -> float:
    """
    Calculates purchase intent score (0-100).
    Deep Learning impulse probability lowers intent contribution via damping factor.
    """
    ans = features.get("raw_answers", {})
    planned = ans.get("planned_status", "")
    delay = ans.get("delay_7days", "")

    if planned == "planned":
        base = 90.0
    elif planned == "discount_saw":
        base = 50.0
    elif planned == "social_ad":
        base = 35.0
    else:
        base = 25.0

    if delay == "urgent_today":
        base = min(100.0, base + 10.0)
    elif delay == "can_wait":
        base = max(0.0, base - 5.0)

    # Damping by Deep Learning impulse probability:
    # High impulse probability reduces the purchase intent contribution by up to 50%
    damped_intent = base * (1.0 - (0.50 * impulse_prob))
    return round(damped_intent, 1)


def calculate_behavior_score(features: Dict[str, Any], impulse_prob: float) -> float:
    """
    Calculates behavior score (0-100) reflecting financial discipline and regret history.
    High DL impulse probability further dampens this score.
    """
    regret_rate = features.get("previous_regret_rate", 0.15)
    recent_purchases = features.get("recent_purchases", 0)

    base = 100.0 - (regret_rate * 45.0) - (min(recent_purchases, 6) * 5.0)
    base = max(10.0, min(100.0, base))

    # Damping by Deep Learning impulse probability:
    # Up to 40% reduction for high predicted impulse risk
    damped_behavior = base * (1.0 - (0.40 * impulse_prob))
    return round(damped_behavior, 1)


def determine_recommendation(
    total_score: float, features: Dict[str, Any]
) -> str:
    """
    75-100 BUY NOW | 50-74 CONSIDER | 25-49 WAIT 7 DAYS | 0-24 DON'T BUY
    Exception: If essential product is broken and item is a genuine replacement,
    do NOT blindly recommend waiting.
    """
    ans = features.get("raw_answers", {})
    cond = ans.get("existing_condition", "")
    impact = ans.get("broken_impact", "")
    is_broken_replacement = (cond == "broken") and (impact in ["critical", "manageable"])

    if total_score >= 75.0:
        recommendation = "BUY NOW"
    elif total_score >= 50.0:
        recommendation = "CONSIDER"
    elif total_score >= 25.0:
        recommendation = "WAIT 7 DAYS"
    else:
        recommendation = "DON'T BUY"

    # Exception rule:
    if is_broken_replacement and recommendation in ["WAIT 7 DAYS", "DON'T BUY"]:
        recommendation = "CONSIDER" if total_score < 65.0 else "BUY NOW"

    return recommendation


def generate_factors_and_reasons(
    features: Dict[str, Any], impulse_prob: float, total_score: float
) -> Tuple[List[str], List[str]]:
    """Generates transparent, explainable positive factors and caution reasons."""
    positive = []
    reasons = []

    ans = features.get("raw_answers", {})
    cond = ans.get("existing_condition", "")
    similar_items = features.get("similar_owned_items", [])
    ratio = features.get("price_to_budget_ratio", 0.0)
    planned = ans.get("planned_status", "")
    usage = ans.get("usage_frequency", "")

    # Check existing item
    if similar_items and cond == "working_fine":
        owned_name = similar_items[0]["product_name"]
        reasons.append(f"You already own '{owned_name}', which is working fine without major issues.")
    elif cond == "broken":
        positive.append("Your existing item is broken, making this a legitimate functional replacement.")

    # Check planning & intent
    if planned == "planned":
        positive.append("This is an intentionally planned purchase that you have considered over time.")
    elif planned == "discount_saw":
        reasons.append("Your interest appears sparked primarily by a sale/discount alert rather than a premeditated need.")
    elif planned == "social_ad":
        reasons.append("This purchase decision is influenced by social media advertising algorithms.")
    elif planned == "browsing_impulse":
        reasons.append("This appears to be an spontaneous browsing impulse.")

    # Check impulse probability
    if impulse_prob >= 0.65:
        reasons.append(f"Deep Learning model detected elevated impulse patterns ({int(impulse_prob * 100)}% probability).")
    elif impulse_prob <= 0.30:
        positive.append(f"Deep Learning model evaluated low impulse indicators ({int(impulse_prob * 100)}% probability).")

    # Check usage
    if usage == "daily":
        positive.append("You plan to use this item every day, maximizing cost-per-use value.")
    elif usage in ["monthly", "rarely"]:
        reasons.append("Projected infrequent usage suggests low cost-per-use efficiency.")

    # Check budget
    if ratio > 0.35:
        reasons.append(f"Item price represents {ratio * 100:.1f}% of your monthly budget, which strains savings.")
    elif ratio <= 0.10:
        positive.append("Item price is well within healthy discretionary budget margins.")

    if not positive:
        positive.append("The item addresses a specific functional interest or upgrade.")
    if not reasons:
        reasons.append("No critical spending warnings detected for this item.")

    return positive, reasons


def compute_comprehensive_score(
    features: Dict[str, Any], impulse_prob: float
) -> Dict[str, Any]:
    """Computes all factor scores, total purchase score, and recommendation."""
    need_score = calculate_need_score(features)
    usage_score = calculate_usage_score(features)
    budget_score = calculate_budget_score(features)
    existing_score = calculate_existing_product_score(features)
    intent_score = calculate_purchase_intent_score(features, impulse_prob)
    behavior_score = calculate_behavior_score(features, impulse_prob)

    total_score = (
        (need_score * SCORING_WEIGHTS["need"])
        + (usage_score * SCORING_WEIGHTS["usage"])
        + (budget_score * SCORING_WEIGHTS["budget"])
        + (existing_score * SCORING_WEIGHTS["existing_product"])
        + (intent_score * SCORING_WEIGHTS["purchase_intent"])
        + (behavior_score * SCORING_WEIGHTS["behavior"])
    )

    total_score = round(max(0.0, min(100.0, total_score)), 1)
    recommendation = determine_recommendation(total_score, features)
    positive_factors, reasons = generate_factors_and_reasons(features, impulse_prob, total_score)

    need_level = "High" if need_score >= 70 else ("Moderate" if need_score >= 40 else "Low")

    return {
        "purchase_score": total_score,
        "impulse_probability": impulse_prob,
        "need_score": round(need_score, 1),
        "need_level": need_level,
        "usage_score": round(usage_score, 1),
        "budget_score": round(budget_score, 1),
        "existing_score": round(existing_score, 1),
        "intent_score": round(intent_score, 1),
        "behavior_score": round(behavior_score, 1),
        "recommendation": recommendation,
        "positive_factors": positive_factors,
        "reasons": reasons,
        "confidence": 0.88,
    }
