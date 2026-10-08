from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    monthly_budget = Column(Float, default=20000.0, nullable=False)
    personality = Column(String(50), default="Best Friend", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    my_stuff = relationship("MyStuff", back_populates="user", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=True)
    category = Column(String(100), default="General", nullable=False)
    price = Column(Float, nullable=False)
    product_url = Column(String(500), nullable=True)
    image_path = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analyses = relationship("Analysis", back_populates="product")
    purchases = relationship("Purchase", back_populates="product")


class MyStuff(Base):
    __tablename__ = "my_stuff"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    purchase_date = Column(String(50), nullable=True)
    price = Column(Float, default=0.0, nullable=False)
    condition = Column(String(50), default="Working", nullable=False)  # Working, Broken, Minor issues
    usage_frequency = Column(String(50), default="Daily", nullable=False)  # Daily, Weekly, Rarely, Never

    user = relationship("User", back_populates="my_stuff")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    satisfaction = Column(String(50), nullable=True)  # Very satisfied, Satisfied, Neutral, Regret, Strong regret
    used_frequency = Column(String(50), nullable=True)
    regret = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="purchases")
    product = relationship("Product", back_populates="purchases")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    purchase_score = Column(Float, default=0.0, nullable=False)  # 0-100
    impulse_probability = Column(Float, default=0.0, nullable=False)  # 0.0-1.0
    need_score = Column(Float, default=0.0, nullable=False)  # 0-100
    budget_score = Column(Float, default=0.0, nullable=False)  # 0-100
    recommendation = Column(String(50), default="CONSIDER", nullable=False)  # BUY NOW, CONSIDER, WAIT 7 DAYS, DON'T BUY
    confidence = Column(Float, default=0.85, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="analyses")
    product = relationship("Product", back_populates="analyses")
    question_answers = relationship("QuestionAnswer", back_populates="analysis", cascade="all, delete-orphan")
    wait_record = relationship("WaitRecord", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="question_answers")


class WaitRecord(Base):
    __tablename__ = "wait_records"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    wait_days = Column(Integer, default=7, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    recheck_date = Column(DateTime, nullable=False)
    final_decision = Column(String(50), nullable=True)  # Bought, Did not buy, Still deciding

    analysis = relationship("Analysis", back_populates="wait_record")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    purchased = Column(Boolean, nullable=False)
    satisfaction = Column(String(50), nullable=True)
    regret = Column(Boolean, default=False, nullable=False)
    feedback_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="feedback")
