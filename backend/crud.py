from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models import (
    User,
    Product,
    MyStuff,
    Purchase,
    Analysis,
    QuestionAnswer,
    WaitRecord,
    Feedback,
)
from backend.schemas import (
    UserCreate,
    UserUpdate,
    ProductCreate,
    MyStuffCreate,
    PurchaseCreate,
    FeedbackCreate,
)
from backend.utils.security import hash_password


# User CRUD
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        monthly_budget=user.monthly_budget,
        personality=user.personality,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_personality(db: Session, user_id: int, personality: str) -> Optional[User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db_user.personality = personality
    db.commit()
    db.refresh(db_user)
    return db_user


# Product CRUD
def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(
        name=product.name,
        brand=product.brand,
        category=product.category,
        price=product.price,
        product_url=product.product_url,
        image_path=product.image_path,
        description=product.description,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# MyStuff CRUD
def get_my_stuff_by_user(db: Session, user_id: int) -> List[MyStuff]:
    return db.query(MyStuff).filter(MyStuff.user_id == user_id).all()


def get_my_stuff_item(db: Session, item_id: int) -> Optional[MyStuff]:
    return db.query(MyStuff).filter(MyStuff.id == item_id).first()


def create_my_stuff(db: Session, item: MyStuffCreate) -> MyStuff:
    db_item = MyStuff(
        user_id=item.user_id,
        product_name=item.product_name,
        category=item.category,
        purchase_date=item.purchase_date,
        price=item.price,
        condition=item.condition,
        usage_frequency=item.usage_frequency,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_my_stuff(db: Session, item_id: int) -> bool:
    item = get_my_stuff_item(db, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


# Purchase CRUD
def get_purchases_by_user(db: Session, user_id: int) -> List[Purchase]:
    return (
        db.query(Purchase)
        .filter(Purchase.user_id == user_id)
        .order_by(Purchase.purchase_date.desc())
        .all()
    )


def create_purchase(db: Session, purchase: PurchaseCreate) -> Purchase:
    db_purchase = Purchase(
        user_id=purchase.user_id,
        product_id=purchase.product_id,
        price=purchase.price,
        category=purchase.category,
        satisfaction=purchase.satisfaction,
        used_frequency=purchase.used_frequency,
        regret=purchase.regret,
        purchase_date=purchase.purchase_date or datetime.utcnow(),
    )
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase


# Analysis CRUD
def get_analysis(db: Session, analysis_id: int) -> Optional[Analysis]:
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()


def get_analyses_by_user(db: Session, user_id: int) -> List[Analysis]:
    return (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )


def create_analysis(db: Session, user_id: int, product_id: int) -> Analysis:
    db_analysis = Analysis(
        user_id=user_id,
        product_id=product_id,
        purchase_score=0.0,
        impulse_probability=0.0,
        need_score=0.0,
        budget_score=0.0,
        recommendation="CONSIDER",
        confidence=0.85,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def update_analysis_scores(
    db: Session,
    analysis_id: int,
    purchase_score: float,
    impulse_probability: float,
    need_score: float,
    budget_score: float,
    recommendation: str,
    confidence: float,
) -> Optional[Analysis]:
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        return None
    analysis.purchase_score = purchase_score
    analysis.impulse_probability = impulse_probability
    analysis.need_score = need_score
    analysis.budget_score = budget_score
    analysis.recommendation = recommendation
    analysis.confidence = confidence
    db.commit()
    db.refresh(analysis)
    return analysis


# QuestionAnswer CRUD
def create_question_answer(
    db: Session, analysis_id: int, question: str, answer: str
) -> QuestionAnswer:
    qa = QuestionAnswer(
        analysis_id=analysis_id,
        question=question,
        answer=answer,
        created_at=datetime.utcnow(),
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return qa


def get_answers_for_analysis(db: Session, analysis_id: int) -> List[QuestionAnswer]:
    return (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.analysis_id == analysis_id)
        .order_by(QuestionAnswer.created_at.asc())
        .all()
    )


# WaitRecord CRUD
def create_wait_record(db: Session, analysis_id: int, wait_days: int = 7) -> WaitRecord:
    now = datetime.utcnow()
    recheck = now + timedelta(days=wait_days)
    record = WaitRecord(
        analysis_id=analysis_id,
        wait_days=wait_days,
        start_date=now,
        recheck_date=recheck,
        final_decision=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_wait_record_by_analysis(db: Session, analysis_id: int) -> Optional[WaitRecord]:
    return db.query(WaitRecord).filter(WaitRecord.analysis_id == analysis_id).first()


def update_wait_decision(
    db: Session, analysis_id: int, final_decision: str
) -> Optional[WaitRecord]:
    record = get_wait_record_by_analysis(db, analysis_id)
    if not record:
        return None
    record.final_decision = final_decision
    db.commit()
    db.refresh(record)
    return record


# Feedback CRUD
def create_feedback(db: Session, feedback: FeedbackCreate) -> Feedback:
    db_feedback = Feedback(
        analysis_id=feedback.analysis_id,
        purchased=feedback.purchased,
        satisfaction=feedback.satisfaction,
        regret=feedback.regret,
        feedback_date=datetime.utcnow(),
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback_by_analysis(db: Session, analysis_id: int) -> Optional[Feedback]:
    return db.query(Feedback).filter(Feedback.analysis_id == analysis_id).first()
