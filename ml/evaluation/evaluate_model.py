"""ml/evaluation/evaluate_model.py

Evaluates the trained Impulse Probability Deep Learning Model on the test set.
Computes and prints:
- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC
- Confusion Matrix
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import joblib
import numpy as np
import tensorflow as tf
from keras import models
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)


def evaluate():
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
    model_path = os.path.join(models_dir, "impulse_model.keras")
    test_data_path = os.path.join(models_dir, "test_data.pkl")

    if not os.path.exists(model_path) or not os.path.exists(test_data_path):
        raise FileNotFoundError(
            f"Model or test data not found in {models_dir}. Please run ml/training/train_model.py first."
        )

    model = models.load_model(model_path)
    test_data = joblib.load(test_data_path)
    X_test = test_data["X_test"]
    y_test = test_data["y_test"]

    # Predict probabilities and classes
    y_probs = model.predict(X_test, verbose=0).ravel()
    y_pred = (y_probs >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_probs)
    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "=" * 50)
    print("      DEEP LEARNING MODEL EVALUATION REPORT")
    print("=" * 50)
    print(f"Total Test Samples:   {len(y_test)}")
    print(f"Accuracy:             {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Precision:            {prec:.4f} ({prec * 100:.2f}%)")
    print(f"Recall:               {rec:.4f} ({rec * 100:.2f}%)")
    print(f"F1 Score:             {f1:.4f}")
    print(f"ROC-AUC:              {auc:.4f}")
    print("\nConfusion Matrix:")
    print("               Predicted Non-Impulse | Predicted Impulse")
    print(f"Actual Non-Impulse:        {cm[0][0]:<10} | {cm[0][1]:<10}")
    print(f"Actual Impulse:            {cm[1][0]:<10} | {cm[1][1]:<10}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Non-Impulse (0)", "Impulse (1)"]))
    print("=" * 50)

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "confusion_matrix": cm.tolist(),
    }


if __name__ == "__main__":
    evaluate()
