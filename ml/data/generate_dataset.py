"""ml/data/generate_dataset.py

Synthetic dataset generator for BuyLater impulse purchase prediction.

DISCLAIMER:
"This is synthetic prototype data created to demonstrate the Deep Learning pipeline."
Do NOT claim it represents real human psychology.
"""

import os
import numpy as np
import pandas as pd


def generate_synthetic_data(n_samples: int = 3000, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)

    # 1. Monthly budget
    monthly_budget = np.random.choice([10000, 20000, 35000, 50000, 75000, 100000], size=n_samples, p=[0.15, 0.35, 0.25, 0.15, 0.07, 0.03])

    # 2. Price
    price = np.random.exponential(scale=3500, size=n_samples) + 200
    price = np.round(np.clip(price, 100, 80000), 2)

    # 3. Price to budget ratio
    price_to_budget_ratio = np.round(price / (monthly_budget + 1e-5), 4)

    # 4. Similar item owned (0 or 1)
    similar_item_owned = np.random.binomial(n=1, p=0.45, size=n_samples)

    # 5. Existing item working (if owned: 0 or 1, else 0)
    existing_item_working = np.where(
        similar_item_owned == 1,
        np.random.binomial(n=1, p=0.75, size=n_samples),
        0
    )

    # 6. Planned purchase (0 or 1)
    planned_purchase = np.random.binomial(n=1, p=0.40, size=n_samples)

    # 7. Expected usage (days per month: Daily=30, Weekly=4, Rarely=1, Never=0)
    expected_usage = np.random.choice([0, 1, 4, 15, 30], size=n_samples, p=[0.05, 0.20, 0.35, 0.20, 0.20])

    # 8. Recent purchases in last 30 days
    recent_purchases = np.random.poisson(lam=3.0, size=n_samples)

    # 9. Recent spending in last 30 days
    recent_spending = np.round(recent_purchases * np.random.uniform(500, 4000, size=n_samples), 2)

    # 10. Average purchase value
    average_purchase_value = np.round(np.where(recent_purchases > 0, recent_spending / recent_purchases, 1500), 2)

    # 11. Category purchase count
    category_purchase_count = np.random.poisson(lam=1.5, size=n_samples)

    # 12. Days since last purchase
    days_since_last_purchase = np.random.geometric(p=0.08, size=n_samples)
    days_since_last_purchase = np.clip(days_since_last_purchase, 0, 90)

    # 13. Discount present (0 or 1)
    discount_present = np.random.binomial(n=1, p=0.55, size=n_samples)

    # 14. Social media influence (0 or 1)
    social_media_influence = np.random.binomial(n=1, p=0.38, size=n_samples)

    # 15. Sale influence (0 or 1)
    sale_influence = np.random.binomial(n=1, p=0.45, size=n_samples)

    # 16. Purchase reason
    reasons = ["genuine_need", "replacement", "upgrade", "discount", "social_media", "looks_cool", "boredom"]
    purchase_reason = np.random.choice(
        reasons,
        size=n_samples,
        p=[0.20, 0.15, 0.18, 0.17, 0.12, 0.10, 0.08]
    )

    # 17. Previous regret rate (0.0 to 1.0)
    previous_regret_rate = np.round(np.random.beta(a=2, b=5, size=n_samples), 3)

    # Realistic Ground Truth calculation for impulse probability
    # Impulse score increases with unplanned, discount/sale/social media, working duplicate, high price ratio, high regret
    # Impulse score decreases with planned, genuine need/replacement, daily usage, broken item
    logits = (
        -1.2  # baseline bias
        - 1.8 * planned_purchase
        + 0.8 * (similar_item_owned * existing_item_working)
        - 0.9 * (similar_item_owned * (1 - existing_item_working))  # broken item replacement is not impulse
        + 0.7 * discount_present
        + 0.8 * sale_influence
        + 0.9 * social_media_influence
        + 1.5 * np.clip(price_to_budget_ratio * 3.0, 0, 2.5)
        - 0.04 * expected_usage
        + 0.15 * np.clip(recent_purchases, 0, 8)
        + 1.2 * previous_regret_rate
        - 0.02 * days_since_last_purchase
    )

    # Add reason effects
    reason_effects = {
        "genuine_need": -1.5,
        "replacement": -1.2,
        "upgrade": 0.1,
        "discount": 0.8,
        "social_media": 1.0,
        "looks_cool": 1.2,
        "boredom": 1.4,
    }
    reason_vals = np.array([reason_effects[r] for r in purchase_reason])
    logits += reason_vals

    # Add realistic noise so accuracy is realistic (~82-87%, not 100%)
    noise = np.random.normal(loc=0.0, scale=0.9, size=n_samples)
    logits += noise

    # Logistic sigmoid
    prob = 1.0 / (1.0 + np.exp(-logits))
    impulse_purchase = (prob >= 0.5).astype(int)

    df = pd.DataFrame({
        "price": price,
        "monthly_budget": monthly_budget,
        "price_to_budget_ratio": price_to_budget_ratio,
        "similar_item_owned": similar_item_owned,
        "existing_item_working": existing_item_working,
        "planned_purchase": planned_purchase,
        "expected_usage": expected_usage,
        "recent_purchases": recent_purchases,
        "recent_spending": recent_spending,
        "average_purchase_value": average_purchase_value,
        "category_purchase_count": category_purchase_count,
        "days_since_last_purchase": days_since_last_purchase,
        "discount_present": discount_present,
        "social_media_influence": social_media_influence,
        "sale_influence": sale_influence,
        "purchase_reason": purchase_reason,
        "previous_regret_rate": previous_regret_rate,
        "impulse_purchase": impulse_purchase,
    })

    return df


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_spending_data.csv")

    data = generate_synthetic_data(n_samples=3200, random_state=42)
    data.to_csv(out_path, index=False)
    print(f"Generated {len(data)} samples saved to {out_path}")
    print(f"Impulse class balance: {data['impulse_purchase'].value_counts(normalize=True).to_dict()}")
