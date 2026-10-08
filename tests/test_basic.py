"""tests/test_basic.py

Unit tests for BuyLater core services and modules:
- User management
- Product creation & OCR
- My Stuff explainable similarity
- History statistics
- Behavior feature engineering
- Deep Learning model inference
- Scoring engine
- Personality formatting
"""

import os
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.models import User, Product, MyStuff, Purchase
from backend.services.my_stuff_service import calculate_item_similarity, find_similar_owned_items
from backend.services.history_service import get_user_history_stats
from backend.services.behavior_service import extract_behavior_features
from backend.services.scoring_service import compute_comprehensive_score
from backend.services.product_service import extract_from_image
from backend.ai.impulse_model import predict_impulse_probability
from backend.utils.personality import format_personality_explanation

from backend.main import app, seed_demo_user

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    seed_demo_user()
    yield


def test_user_creation_and_retrieval():
    # Fetch or verify demo user
    resp = client.get("/users/1")
    assert resp.status_code == 200
    user_data = resp.json()
    assert user_data["id"] == 1
    assert "email" in user_data


def test_product_manual_creation():
    payload = {
        "name": "Sony Wireless Headphones Test",
        "brand": "Sony",
        "category": "Electronics",
        "price": 7999.0,
        "product_url": "https://example.com/sony-test",
        "description": "Premium active noise cancellation",
    }
    resp = client.post("/products/manual", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload["name"]
    assert data["price"] == 7999.0
    assert data["id"] is not None


def test_ocr_extraction_small_sample(tmp_path):
    # Generate a small image with price and text
    img_path = str(tmp_path / "test_ocr_product.png")
    img = Image.new("RGB", (400, 150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Sony Headphone", fill=(0, 0, 0))
    draw.text((20, 50), "Price Rs. 4999", fill=(0, 0, 0))
    draw.text((20, 80), "20% off", fill=(0, 0, 0))
    img.save(img_path)

    extracted = extract_from_image(img_path)
    assert extracted["extraction_source"] == "ocr"
    assert "raw_text" in extracted
    # Should detect price around 4999 or extracted raw text
    assert len(extracted["raw_text"]) > 0


def test_my_stuff_similarity():
    # Sony Headphones vs JBL Headphones in Electronics
    sim = calculate_item_similarity(
        candidate_name="Sony WH-1000XM4 Headphones",
        candidate_category="Electronics",
        owned_name="JBL Live 650 Wireless Headphones",
        owned_category="Electronics",
    )
    assert sim >= 0.50, f"Expected category + keyword similarity >= 0.50, got {sim}"


def test_dl_model_prediction():
    features = {
        "price": 25000.0,
        "monthly_budget": 20000.0,
        "price_to_budget_ratio": 1.25,
        "similar_item_owned": 1,
        "existing_item_working": 1,
        "planned_purchase": 0,
        "expected_usage": 1,
        "recent_purchases": 5,
        "recent_spending": 18000.0,
        "average_purchase_value": 3600.0,
        "category_purchase_count": 3,
        "days_since_last_purchase": 2,
        "discount_present": 1,
        "social_media_influence": 1,
        "sale_influence": 1,
        "purchase_reason": "looks_cool",
        "previous_regret_rate": 0.50,
    }
    prob = predict_impulse_probability(features)
    assert 0.0 <= prob <= 1.0
    # High impulse indicators should yield elevated impulse probability
    assert prob >= 0.50, f"Expected elevated impulse probability, got {prob}"


def test_scoring_service():
    features = {
        "price_to_budget_ratio": 0.05,
        "expected_usage": 30,
        "similar_item_owned": 0,
        "previous_regret_rate": 0.05,
        "recent_purchases": 1,
        "raw_answers": {
            "planned_status": "planned",
            "usage_frequency": "daily",
            "budget_feeling": "comfortable",
        },
    }
    res = compute_comprehensive_score(features, impulse_prob=0.08)
    assert res["purchase_score"] >= 70.0
    assert res["recommendation"] in ["BUY NOW", "CONSIDER"]
    assert len(res["positive_factors"]) > 0


def test_personality_formatting():
    explanation = format_personality_explanation(
        personality="Best Friend",
        recommendation="DON'T BUY",
        product_name="Golden Watch",
        score=22.0,
        impulse_prob=0.88,
        reasons=["You already own a functional watch", "Unplanned browsing discovery"],
        positive_factors=["Nice design"],
    )
    assert "Hard pass" in explanation or "bro" in explanation.lower() or "Golden Watch" in explanation
