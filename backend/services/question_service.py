"""backend/services/question_service.py

Adaptive Question Engine:
Delivers one question at a time using a rule/decision tree based on answers provided so far.
Never asks repetitive or irrelevant questions.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import QuestionAnswer, Product
from backend.services.my_stuff_service import find_similar_owned_items

QUESTION_NODES = {
    "planned_status": {
        "text": "Was this purchase planned in advance, or did you just come across it?",
        "type": "choice",
        "options": [
            {"label": "Planned for weeks/months", "value": "planned"},
            {"label": "Saw a sale or limited-time discount", "value": "discount_saw"},
            {"label": "Saw an ad or social media post", "value": "social_ad"},
            {"label": "Just browsing and it looks cool", "value": "browsing_impulse"},
        ],
    },
    "similar_item": {
        "text": "Do you already own something similar that can do a comparable job?",
        "type": "choice",
        "options": [
            {"label": "Yes, I already own something similar", "value": "yes_similar"},
            {"label": "No, I don't have anything like this", "value": "no_similar"},
        ],
    },
    "existing_condition": {
        "text": "Is your current similar item still working?",
        "type": "choice",
        "options": [
            {"label": "Yes, it is working fine", "value": "working_fine"},
            {"label": "No, it is broken or unusable", "value": "broken"},
            {"label": "It has minor issues or feels outdated", "value": "minor_issues"},
        ],
    },
    "upgrade_reason": {
        "text": "Since your current item works, what does this new one actually offer?",
        "type": "choice",
        "options": [
            {"label": "Essential new feature needed for work/study", "value": "essential_feature"},
            {"label": "Slight improvement in specs / aesthetic upgrade", "value": "minor_upgrade"},
            {"label": "Mostly novelty / just want the newer version", "value": "novelty"},
        ],
    },
    "broken_impact": {
        "text": "How much does the broken item disrupt your daily routine or studies?",
        "type": "choice",
        "options": [
            {"label": "Critical disruption, I cannot function without it", "value": "critical"},
            {"label": "Inconvenient, but I can manage temporarily", "value": "manageable"},
            {"label": "Minor inconvenience, rarely used anyway", "value": "minor"},
        ],
    },
    "usage_frequency": {
        "text": "How often do you realistically anticipate using this item?",
        "type": "choice",
        "options": [
            {"label": "Every day (Daily)", "value": "daily"},
            {"label": "Several times a week", "value": "weekly"},
            {"label": "A couple times a month", "value": "monthly"},
            {"label": "Rarely or for single-use", "value": "rarely"},
        ],
    },
    "delay_7days": {
        "text": "What happens if you hold off and wait 7 days before deciding?",
        "type": "choice",
        "options": [
            {"label": "Nothing bad happens, I can easily wait 7 days", "value": "can_wait"},
            {"label": "The discount or deal might expire", "value": "deal_expires"},
            {"label": "I have an urgent deadline/need today", "value": "urgent_today"},
        ],
    },
    "budget_feeling": {
        "text": "How does spending this amount feel against your monthly budget?",
        "type": "choice",
        "options": [
            {"label": "Well within my spending budget", "value": "comfortable"},
            {"label": "A bit tight, but I can manage", "value": "manageable"},
            {"label": "Stretching my budget / might cause stress", "value": "stretched"},
        ],
    },
}


def get_next_question(
    db: Session, analysis_id: int, user_id: int, product: Product
) -> Dict[str, Any]:
    """Evaluates answered questions and returns the next adaptive question."""
    existing_answers = (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.analysis_id == analysis_id)
        .all()
    )

    answered_keys = {qa.question for qa in existing_answers}
    answer_dict = {qa.question: qa.answer for qa in existing_answers}

    # Total questions in a typical sequence is around 5
    # Determine the next question key based on the decision tree
    next_key: Optional[str] = None

    if "planned_status" not in answered_keys:
        next_key = "planned_status"

    elif "similar_item" not in answered_keys:
        # Check if database MyStuff already found similar items
        similar_items = find_similar_owned_items(db, user_id, product)
        if similar_items:
            # We already know user has a similar item, go straight to condition
            next_key = "existing_condition"
        else:
            next_key = "similar_item"

    elif (
        answer_dict.get("similar_item") == "yes_similar"
        and "existing_condition" not in answered_keys
    ):
        next_key = "existing_condition"

    elif (
        answer_dict.get("existing_condition") == "working_fine"
        and "upgrade_reason" not in answered_keys
    ):
        next_key = "upgrade_reason"

    elif (
        answer_dict.get("existing_condition") == "broken"
        and "broken_impact" not in answered_keys
    ):
        next_key = "broken_impact"

    elif "usage_frequency" not in answered_keys:
        next_key = "usage_frequency"

    elif "delay_7days" not in answered_keys:
        next_key = "delay_7days"

    elif "budget_feeling" not in answered_keys:
        next_key = "budget_feeling"

    if next_key is None:
        # All required questions answered!
        return {
            "question_key": "complete",
            "question_text": "All questions completed. Ready to calculate final score.",
            "question_type": "complete",
            "options": [],
            "is_final": True,
            "progress_percentage": 100,
        }

    q_info = QUESTION_NODES[next_key]
    answered_count = len(answered_keys)
    # Estimate total ~ 5
    progress = min(95, int((answered_count / 5.0) * 100))

    return {
        "question_key": next_key,
        "question_text": q_info["text"],
        "question_type": q_info["type"],
        "options": q_info["options"],
        "is_final": False,
        "progress_percentage": progress,
    }
