"""ml/preprocessing/preprocess.py

Feature preprocessing pipeline for impulse purchase prediction.
Handles numerical scaling, categorical encoding, and feature alignment.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder

NUMERIC_FEATURES = [
    "price",
    "monthly_budget",
    "price_to_budget_ratio",
    "similar_item_owned",
    "existing_item_working",
    "planned_purchase",
    "expected_usage",
    "recent_purchases",
    "recent_spending",
    "average_purchase_value",
    "category_purchase_count",
    "days_since_last_purchase",
    "discount_present",
    "social_media_influence",
    "sale_influence",
    "previous_regret_rate",
]

CATEGORICAL_FEATURES = ["purchase_reason"]
CATEGORIES_LIST = [["genuine_need", "replacement", "upgrade", "discount", "social_media", "looks_cool", "boredom"]]


def fit_preprocessor(df: pd.DataFrame):
    """Fits scaler on numeric features and encoder on categorical features."""
    scaler = StandardScaler()
    scaler.fit(df[NUMERIC_FEATURES])

    encoder = OneHotEncoder(categories=CATEGORIES_LIST, handle_unknown="ignore", sparse_output=False)
    encoder.fit(df[CATEGORICAL_FEATURES])

    encoded_cat_names = encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_feature_names = NUMERIC_FEATURES + encoded_cat_names

    return scaler, encoder, all_feature_names


def transform_data(df: pd.DataFrame, scaler, encoder):
    """Transforms raw DataFrame to numpy array with exact feature order."""
    num_scaled = scaler.transform(df[NUMERIC_FEATURES])
    cat_encoded = encoder.transform(df[CATEGORICAL_FEATURES])
    X = np.hstack([num_scaled, cat_encoded])
    return X


def transform_single_instance(features: dict, scaler, encoder, feature_names: list) -> np.ndarray:
    """Transforms a single feature dictionary into model input array (1, num_features)."""
    # Ensure default values for any missing feature
    clean_dict = {
        "price": float(features.get("price", 1000.0)),
        "monthly_budget": float(features.get("monthly_budget", 20000.0)),
        "price_to_budget_ratio": float(
            features.get(
                "price_to_budget_ratio",
                float(features.get("price", 1000.0)) / (float(features.get("monthly_budget", 20000.0)) + 1e-5),
            )
        ),
        "similar_item_owned": int(features.get("similar_item_owned", 0)),
        "existing_item_working": int(features.get("existing_item_working", 0)),
        "planned_purchase": int(features.get("planned_purchase", 0)),
        "expected_usage": int(features.get("expected_usage", 4)),
        "recent_purchases": int(features.get("recent_purchases", 0)),
        "recent_spending": float(features.get("recent_spending", 0.0)),
        "average_purchase_value": float(features.get("average_purchase_value", 0.0)),
        "category_purchase_count": int(features.get("category_purchase_count", 0)),
        "days_since_last_purchase": int(features.get("days_since_last_purchase", 15)),
        "discount_present": int(features.get("discount_present", 0)),
        "social_media_influence": int(features.get("social_media_influence", 0)),
        "sale_influence": int(features.get("sale_influence", 0)),
        "purchase_reason": str(features.get("purchase_reason", "genuine_need")),
        "previous_regret_rate": float(features.get("previous_regret_rate", 0.0)),
    }

    df_single = pd.DataFrame([clean_dict])
    X_single = transform_data(df_single, scaler, encoder)
    return X_single
