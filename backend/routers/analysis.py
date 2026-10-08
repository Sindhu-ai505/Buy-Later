"""backend/routers/analysis.py

API router for the end-to-end spending analysis workflow:
- Start analysis session
- Step-by-step adaptive questions
- Feature engineering & Deep Learning inference
- Scoring engine & recommendation
- Personality-toned explanations
- Decision challenge (Devil's Advocate)
- 7-day cooling-off wait timer & re-evaluation
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    AnalysisStart,
    AnalysisResponse,
    AnalysisResultResponse,
    NextQuestionResponse,
    QuestionAnswerSubmit,
    ChallengeResponse,
    WaitRecordCreate,
    WaitDecisionUpdate,
    WaitRecordResponse,
    ProductResponse,
)
from backend.crud import (
    get_analysis,
    create_analysis,
    update_analysis_scores,
    create_question_answer,
    get_product,
    get_user,
    get_wait_record_by_analysis,
)
from backend.services.question_service import get_next_question
from backend.services.behavior_service import extract_behavior_features
from backend.services.scoring_service import compute_comprehensive_score
from backend.services.challenge_service import generate_challenge
from backend.services.wait_service import (
    initiate_wait,
    get_wait_status,
    record_recheck_decision,
)
from backend.services.my_stuff_service import find_similar_owned_items
from backend.ai.impulse_model import predict_impulse_probability
from backend.utils.personality import format_personality_explanation

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/start")
def start_analysis(payload: AnalysisStart, db: Session = Depends(get_db)):
    user = get_user(db, payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    product = get_product(db, payload.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    analysis = create_analysis(db, payload.user_id, payload.product_id)
    first_question = get_next_question(db, analysis.id, user.id, product)

    return {
        "analysis_id": analysis.id,
        "product_id": product.id,
        "user_id": user.id,
        "next_question": first_question,
    }


@router.get("/{analysis_id}")
def get_analysis_info(analysis_id: int, db: Session = Depends(get_db)):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
        )
    product = get_product(db, analysis.product_id)
    next_q = get_next_question(db, analysis.id, analysis.user_id, product)
    return {
        "analysis": AnalysisResponse.from_orm(analysis),
        "next_question": next_q,
    }


@router.post("/{analysis_id}/answer")
def submit_answer(
    analysis_id: int, payload: QuestionAnswerSubmit, db: Session = Depends(get_db)
):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
        )

    # Save question answer
    create_question_answer(
        db,
        analysis_id=analysis_id,
        question=payload.question_key,
        answer=payload.answer,
    )

    product = get_product(db, analysis.product_id)
    user = get_user(db, analysis.user_id)

    # Determine next question
    next_question = get_next_question(db, analysis_id, user.id, product)

    # If all questions are answered, execute ML pipeline & Scoring Engine
    if next_question["is_final"]:
        # 1. Feature Engineering
        features = extract_behavior_features(db, user, product, analysis.id)

        # 2. Deep Learning Impulse Model Inference
        impulse_prob = predict_impulse_probability(features)

        # 3. Explainable Scoring Engine
        score_data = compute_comprehensive_score(features, impulse_prob)

        # 4. Save results to Database
        update_analysis_scores(
            db=db,
            analysis_id=analysis.id,
            purchase_score=score_data["purchase_score"],
            impulse_probability=score_data["impulse_probability"],
            need_score=score_data["need_score"],
            budget_score=score_data["budget_score"],
            recommendation=score_data["recommendation"],
            confidence=score_data["confidence"],
        )

        return {
            "status": "completed",
            "is_final": True,
            "analysis_id": analysis.id,
            "next_question": next_question,
            "summary": {
                "purchase_score": score_data["purchase_score"],
                "impulse_probability": score_data["impulse_probability"],
                "recommendation": score_data["recommendation"],
            },
        }

    return {
        "status": "in_progress",
        "is_final": False,
        "analysis_id": analysis.id,
        "next_question": next_question,
    }


@router.get("/{analysis_id}/result", response_model=AnalysisResultResponse)
def get_analysis_result(analysis_id: int, db: Session = Depends(get_db)):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
        )

    product = get_product(db, analysis.product_id)
    user = get_user(db, analysis.user_id)

    features = extract_behavior_features(db, user, product, analysis.id)
    score_data = compute_comprehensive_score(features, analysis.impulse_probability)
    similar_owned = find_similar_owned_items(db, user.id, product)

    explanation = format_personality_explanation(
        personality=user.personality,
        recommendation=analysis.recommendation,
        product_name=product.name,
        score=analysis.purchase_score,
        impulse_prob=analysis.impulse_probability,
        reasons=score_data["reasons"],
        positive_factors=score_data["positive_factors"],
    )

    return AnalysisResultResponse(
        analysis_id=analysis.id,
        user_id=user.id,
        product_id=product.id,
        product=ProductResponse.from_orm(product),
        purchase_score=analysis.purchase_score,
        impulse_probability=analysis.impulse_probability,
        need_score=analysis.need_score,
        budget_score=analysis.budget_score,
        need_level=score_data["need_level"],
        recommendation=analysis.recommendation,
        confidence=analysis.confidence,
        reasons=score_data["reasons"],
        positive_factors=score_data["positive_factors"],
        personality=user.personality,
        personality_explanation=explanation,
        similar_owned_items=similar_owned,
        created_at=analysis.created_at,
    )


@router.post("/{analysis_id}/challenge", response_model=ChallengeResponse)
def challenge_decision(analysis_id: int, db: Session = Depends(get_db)):
    try:
        challenge_data = generate_challenge(db, analysis_id)
        return ChallengeResponse(**challenge_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/{analysis_id}/wait")
def create_wait_period(
    analysis_id: int, payload: WaitRecordCreate, db: Session = Depends(get_db)
):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
        )
    record = initiate_wait(db, analysis_id, payload.wait_days)
    return {
        "status": "success",
        "message": f"7-day cooling off period initiated. Re-check scheduled.",
        "record_id": record.id,
        "start_date": record.start_date,
        "recheck_date": record.recheck_date,
    }


@router.get("/{analysis_id}/wait")
def check_wait_period(analysis_id: int, db: Session = Depends(get_db)):
    status_info = get_wait_status(db, analysis_id)
    if not status_info.get("exists"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No wait record found"
        )
    return status_info


@router.post("/{analysis_id}/wait/decision")
def submit_wait_decision(
    analysis_id: int, payload: WaitDecisionUpdate, db: Session = Depends(get_db)
):
    try:
        record = record_recheck_decision(db, analysis_id, payload.final_decision)
        return {
            "status": "success",
            "final_decision": record.final_decision,
            "message": "Final decision recorded after cooling-off period.",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
