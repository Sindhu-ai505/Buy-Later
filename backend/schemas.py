from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserBase(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    monthly_budget: float = Field(default=20000.0, ge=0.0)
    personality: str = Field(default="Best Friend")


class UserCreate(UserBase):
    password: str = Field(..., min_length=4)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    monthly_budget: Optional[float] = None
    personality: Optional[str] = None


class PersonalityUpdate(BaseModel):
    personality: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    brand: Optional[str] = None
    category: str = Field(default="General")
    price: float = Field(..., ge=0.0)
    product_url: Optional[str] = None
    image_path: Optional[str] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUrlRequest(BaseModel):
    url: str


class ProductExtractedResponse(BaseModel):
    name: str
    brand: Optional[str] = None
    category: str = "General"
    price: float = 0.0
    product_url: Optional[str] = None
    image_path: Optional[str] = None
    description: Optional[str] = None
    discount: Optional[float] = None
    extraction_source: str  # "url", "ocr", "manual"
    raw_text: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# My Stuff Schemas
class MyStuffBase(BaseModel):
    product_name: str
    category: str
    purchase_date: Optional[str] = None
    price: float = 0.0
    condition: str = "Working"  # Working, Broken, Minor issues
    usage_frequency: str = "Daily"  # Daily, Weekly, Rarely, Never


class MyStuffCreate(MyStuffBase):
    user_id: int


class MyStuffResponse(MyStuffBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# Purchase Schemas
class PurchaseBase(BaseModel):
    product_id: Optional[int] = None
    price: float
    category: str
    satisfaction: Optional[str] = None
    used_frequency: Optional[str] = None
    regret: bool = False


class PurchaseCreate(PurchaseBase):
    user_id: int
    purchase_date: Optional[datetime] = None


class PurchaseResponse(PurchaseBase):
    id: int
    user_id: int
    purchase_date: datetime

    class Config:
        from_attributes = True


# Question Flow Schemas
class QuestionOption(BaseModel):
    label: str
    value: str


class NextQuestionResponse(BaseModel):
    question_key: str
    question_text: str
    question_type: str  # "choice", "text", "boolean"
    options: Optional[List[QuestionOption]] = None
    is_final: bool = False
    progress_percentage: int = 0


class QuestionAnswerSubmit(BaseModel):
    question_key: str
    question: str
    answer: str


# Analysis Schemas
class AnalysisStart(BaseModel):
    user_id: int
    product_id: int


class AnalysisResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    purchase_score: float
    impulse_probability: float
    need_score: float
    budget_score: float
    recommendation: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    analysis_id: int
    user_id: int
    product_id: int
    product: ProductResponse
    purchase_score: float
    impulse_probability: float
    need_score: float
    budget_score: float
    need_level: str
    recommendation: str
    confidence: float
    reasons: List[str]
    positive_factors: List[str]
    personality: str
    personality_explanation: str
    similar_owned_items: List[Dict[str, Any]]
    created_at: datetime


# Challenge Schema
class ChallengeResponse(BaseModel):
    analysis_id: int
    challenge_title: str
    challenge_text: str
    arguments_for_buying: List[str]


# Wait Record Schemas
class WaitRecordCreate(BaseModel):
    wait_days: int = 7


class WaitDecisionUpdate(BaseModel):
    final_decision: str  # "Bought", "Did not buy", "Still deciding"


class WaitRecordResponse(BaseModel):
    id: int
    analysis_id: int
    wait_days: int
    start_date: datetime
    recheck_date: datetime
    final_decision: Optional[str] = None
    is_ready_for_recheck: bool = False

    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackCreate(BaseModel):
    analysis_id: int
    purchased: bool
    satisfaction: Optional[str] = None  # Very satisfied, Satisfied, Neutral, Regret, Strong regret
    regret: bool = False


class FeedbackResponse(BaseModel):
    id: int
    analysis_id: int
    purchased: bool
    satisfaction: Optional[str] = None
    regret: bool
    feedback_date: datetime

    class Config:
        from_attributes = True


# Dashboard Schema
class DashboardResponse(BaseModel):
    user_id: int
    monthly_budget: float
    total_spending: float
    total_purchases: int
    average_purchase: float
    impulse_rate: float
    potential_savings: float
    purchases_avoided: int
    top_category: str
    recent_analyses: List[Dict[str, Any]]
    recent_purchases: List[Dict[str, Any]]
    ai_insights: List[str]
