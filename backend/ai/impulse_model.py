"""backend/ai/impulse_model.py

Loads the trained Keras model and preprocessors to perform impulse purchase inference.
Raises HTTP 503 error if model artifacts are missing.
"""

import os
import joblib
import numpy as np
from fastapi import HTTPException, status
from keras import models
from ml.preprocessing.preprocess import transform_single_instance

# Resolve path to ml/models
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")

MODEL_PATH = os.path.join(MODELS_DIR, "impulse_model.keras")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
ENCODER_PATH = os.path.join(MODELS_DIR, "encoder.pkl")
FEATURES_PATH = os.path.join(MODELS_DIR, "feature_names.pkl")

# Cached instances
_cached_model = None
_cached_scaler = None
_cached_encoder = None
_cached_features = None


def check_artifacts_exist():
    return (
        os.path.exists(MODEL_PATH)
        and os.path.exists(SCALER_PATH)
        and os.path.exists(ENCODER_PATH)
        and os.path.exists(FEATURES_PATH)
    )


def load_model():
    """Loads and caches the model and preprocessor objects."""
    global _cached_model, _cached_scaler, _cached_encoder, _cached_features

    if not check_artifacts_exist():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Run ml/training/train_model.py first. Missing trained model or scaler artifacts.",
        )

    if _cached_model is None:
        _cached_model = models.load_model(MODEL_PATH)
        _cached_scaler = joblib.load(SCALER_PATH)
        _cached_encoder = joblib.load(ENCODER_PATH)
        _cached_features = joblib.load(FEATURES_PATH)

    return _cached_model, _cached_scaler, _cached_encoder, _cached_features


def prepare_features(features_dict: dict) -> np.ndarray:
    """Prepares and scales feature vector using saved preprocessors."""
    _, scaler, encoder, feature_names = load_model()
    return transform_single_instance(features_dict, scaler, encoder, feature_names)


def predict_impulse_probability(features_dict: dict) -> float:
    """Returns predicted impulse probability (0.0 to 1.0) using deep learning model."""
    model, _, _, _ = load_model()
    X = prepare_features(features_dict)
    prob = float(model.predict(X, verbose=0)[0][0])
    return round(float(np.clip(prob, 0.0, 1.0)), 4)
