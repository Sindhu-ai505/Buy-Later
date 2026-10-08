"""ml/data/export_feedback_dataset.py

Exports real user feedback and behavior data from SQLite into a CSV dataset
suitable for future retraining.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
from backend.database import SessionLocal
from backend.models import Analysis, Feedback, Product, User, QuestionAnswer


def export_feedback():
    db = SessionLocal()
    try:
        feedbacks = db.query(Feedback).all()
        if not feedbacks:
            print("No feedback records found in database to export.")
            return

        rows = []
        for fb in feedbacks:
            analysis = db.query(Analysis).filter(Analysis.id == fb.analysis_id).first()
            if not analysis:
                continue
            product = db.query(Product).filter(Product.id == analysis.product_id).first()
            user = db.query(User).filter(User.id == analysis.user_id).first()

            # Target impulse_purchase label:
            # If user bought and felt regret, or did not buy because it was an impulse, label 1.
            # If user bought and was satisfied, label 0.
            is_impulse = 1 if (fb.regret or not fb.purchased) else 0

            rows.append({
                "analysis_id": analysis.id,
                "price": product.price if product else 0.0,
                "monthly_budget": user.monthly_budget if user else 20000.0,
                "purchase_score": analysis.purchase_score,
                "impulse_probability": analysis.impulse_probability,
                "need_score": analysis.need_score,
                "budget_score": analysis.budget_score,
                "recommendation": analysis.recommendation,
                "purchased": 1 if fb.purchased else 0,
                "satisfaction": fb.satisfaction or "None",
                "regret": 1 if fb.regret else 0,
                "target_impulse_label": is_impulse,
                "feedback_date": str(fb.feedback_date),
            })

        df = pd.DataFrame(rows)
        out_dir = os.path.abspath(os.path.dirname(__file__))
        out_path = os.path.join(out_dir, "exported_feedback_data.csv")
        df.to_csv(out_path, index=False)
        print(f"Exported {len(df)} feedback rows to {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    export_feedback()
