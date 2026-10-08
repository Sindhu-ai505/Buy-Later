"""tests/test_end_to_end.py

Complete End-to-End Workflow Test:
Product Creation -> Adaptive Questions -> Feature Engineering ->
Deep Learning Model -> Purchase Score & Recommendation ->
Decision Challenge -> 7-Day Wait -> Post-Decision Feedback.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app, seed_demo_user
from backend.database import Base, engine

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    seed_demo_user()
    yield


def test_full_pipeline_end_to_end():
    # 1. Product creation
    prod_resp = client.post(
        "/products/manual",
        json={
            "name": "Mechanical Keyboard RGB",
            "brand": "Keychron",
            "category": "Electronics",
            "price": 6500.0,
            "description": "Hot-swappable switches",
        },
    )
    assert prod_resp.status_code == 201
    product = prod_resp.json()
    product_id = product["id"]

    # 2. Start analysis session
    start_resp = client.post(
        "/analysis/start",
        json={"user_id": 1, "product_id": product_id},
    )
    assert start_resp.status_code == 200
    session_data = start_resp.json()
    analysis_id = session_data["analysis_id"]
    next_q = session_data["next_question"]

    # 3. Answer questions adaptively until completion
    answers_flow = [
        ("planned_status", "Was this purchase planned?", "browsing_impulse"),
        ("similar_item", "Do you own something similar?", "no_similar"),
        ("usage_frequency", "How often will you use this?", "monthly"),
        ("delay_7days", "What happens if you wait 7 days?", "can_wait"),
        ("budget_feeling", "How does spending feel?", "stretched"),
    ]

    last_resp = None
    for key, q_text, ans_val in answers_flow:
        ans_payload = {
            "question_key": key,
            "question": q_text,
            "answer": ans_val,
        }
        ans_resp = client.post(f"/analysis/{analysis_id}/answer", json=ans_payload)
        assert ans_resp.status_code == 200
        last_resp = ans_resp.json()
        if last_resp.get("is_final"):
            break

    assert last_resp["is_final"] is True
    assert "summary" in last_resp
    assert "purchase_score" in last_resp["summary"]
    assert "impulse_probability" in last_resp["summary"]
    assert "recommendation" in last_resp["summary"]

    # 4. Fetch full result
    result_resp = client.get(f"/analysis/{analysis_id}/result")
    assert result_resp.status_code == 200
    res_data = result_resp.json()
    assert res_data["analysis_id"] == analysis_id
    assert res_data["purchase_score"] >= 0.0
    assert 0.0 <= res_data["impulse_probability"] <= 1.0
    assert res_data["recommendation"] in ["BUY NOW", "CONSIDER", "WAIT 7 DAYS", "DON'T BUY"]
    assert len(res_data["reasons"]) > 0
    assert len(res_data["positive_factors"]) > 0
    assert len(res_data["personality_explanation"]) > 0

    # 5. Challenge My Decision (Devil's Advocate)
    challenge_resp = client.post(f"/analysis/{analysis_id}/challenge")
    assert challenge_resp.status_code == 200
    ch_data = challenge_resp.json()
    assert "challenge_text" in ch_data
    assert len(ch_data["arguments_for_buying"]) > 0

    # 6. Wait 7 Days Cooling Off
    wait_resp = client.post(f"/analysis/{analysis_id}/wait", json={"wait_days": 7})
    assert wait_resp.status_code == 200
    wait_data = wait_resp.json()
    assert wait_data["status"] == "success"

    # Check wait status
    wait_status_resp = client.get(f"/analysis/{analysis_id}/wait")
    assert wait_status_resp.status_code == 200
    assert wait_status_resp.json()["exists"] is True

    # 7. Record Feedback: Avoided purchase (Saved money)
    fb_resp = client.post(
        "/feedback",
        json={
            "analysis_id": analysis_id,
            "purchased": False,
            "satisfaction": "Did not buy",
            "regret": False,
        },
    )
    assert fb_resp.status_code == 201
    fb_data = fb_resp.json()
    assert fb_data["saved_amount"] == 6500.0

    # 8. Check Dashboard reflects potential savings and analytics
    dash_resp = client.get("/dashboard/1")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["potential_savings"] >= 6500.0
    assert dash_data["purchases_avoided"] >= 1
    assert len(dash_data["ai_insights"]) > 0
