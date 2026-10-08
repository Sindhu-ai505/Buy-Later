"""ml/training/train_model.py

Train the Deep Learning model for Impulse Purchase Probability.
Architecture:
Input -> Dense(64, ReLU) -> Dropout -> Dense(32, ReLU) -> Dense(16, ReLU) -> Dense(1, Sigmoid)
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import tensorflow as tf
from keras import layers, models, callbacks, metrics

from ml.data.generate_dataset import generate_synthetic_data
from ml.preprocessing.preprocess import fit_preprocessor, transform_data


def train():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    csv_path = os.path.join(data_dir, "synthetic_spending_data.csv")
    if not os.path.exists(csv_path):
        print("Dataset not found. Generating synthetic dataset...")
        df = generate_synthetic_data(n_samples=3200, random_state=42)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    X_raw = df.drop(columns=["impulse_purchase"])
    y = df["impulse_purchase"].values

    # Stratified Train/Test split (80% train, 20% test)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.20, random_state=42, stratify=y
    )

    # Fit preprocessors on training data only
    scaler, encoder, feature_names = fit_preprocessor(X_train_raw)

    # Transform train and test
    X_train = transform_data(X_train_raw, scaler, encoder)
    X_test = transform_data(X_test_raw, scaler, encoder)

    input_dim = X_train.shape[1]
    print(f"Preprocessed features count: {input_dim}")

    # Build Keras Deep Learning Model
    model = models.Sequential([
        layers.Input(shape=(input_dim,)),
        layers.Dense(64, activation="relu", name="dense_64"),
        layers.Dropout(0.25, name="dropout"),
        layers.Dense(32, activation="relu", name="dense_32"),
        layers.Dense(16, activation="relu", name="dense_16"),
        layers.Dense(1, activation="sigmoid", name="output_sigmoid"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            metrics.Precision(name="precision"),
            metrics.Recall(name="recall"),
            metrics.AUC(name="auc"),
        ],
    )

    early_stop = callbacks.EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True,
        verbose=1,
    )

    print("Training Keras model...")
    history = model.fit(
        X_train,
        y_train,
        validation_split=0.20,
        epochs=50,
        batch_size=32,
        callbacks=[early_stop],
        verbose=1,
    )

    # Save artifacts
    model_path = os.path.join(models_dir, "impulse_model.keras")
    scaler_path = os.path.join(models_dir, "scaler.pkl")
    encoder_path = os.path.join(models_dir, "encoder.pkl")
    features_path = os.path.join(models_dir, "feature_names.pkl")
    test_data_path = os.path.join(models_dir, "test_data.pkl")

    model.save(model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(encoder, encoder_path)
    joblib.dump(feature_names, features_path)
    joblib.dump({"X_test": X_test, "y_test": y_test}, test_data_path)

    print(f"Model saved to {model_path}")
    print(f"Preprocessors saved to {models_dir}")
    return model, X_test, y_test


if __name__ == "__main__":
    train()
