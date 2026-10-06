"""
src/data.py — Data loading, downloading, and preprocessing utilities
for the Q-Interestingness research project.
"""

import os
import urllib.request
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# ── Dataset URLs ──────────────────────────────────────────────────────────────
WINE_QUALITY_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "wine-quality/winequality-red.csv"
)
WINE_QUALITY_RAW = os.path.join("data", "raw", "winequality-red.csv")
WINE_QUALITY_PROCESSED = os.path.join("data", "processed", "wine_quality_processed.csv")

# ── Feature definitions ───────────────────────────────────────────────────────
WINE_FEATURE_COLS = [
    "fixed acidity", "volatile acidity", "citric acid", "residual sugar",
    "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density",
    "pH", "sulphates", "alcohol",
]
WINE_TARGET_COL = "quality"
WINE_QUANTUM_FEATURES = ["alcohol", "volatile acidity", "sulphates", "citric acid"]


def download_wine_quality(dest: str = WINE_QUALITY_RAW, force: bool = False) -> str:
    """Download UCI Red Wine Quality dataset if not already present."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and not force:
        print(f"Dataset already present at: {dest}")
        return dest
    print(f"Downloading wine quality dataset → {dest}")
    urllib.request.urlretrieve(WINE_QUALITY_URL, dest)
    print("Download complete.")
    return dest


def load_wine_quality(path: str = WINE_QUALITY_RAW) -> pd.DataFrame:
    """Load UCI Red Wine Quality dataset."""
    df = pd.read_csv(path, sep=";")
    print(f"Loaded wine quality: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def load_sklearn_wine():
    """Load sklearn wine dataset (178 obs, 13 features, 3 classes)."""
    from sklearn.datasets import load_wine
    bunch = load_wine()
    df = pd.DataFrame(bunch.data, columns=bunch.feature_names)
    df["target"] = bunch.target
    print(f"Loaded sklearn wine: {df.shape[0]} rows × {df.shape[1]} columns")
    return df, bunch.feature_names, "target"


def scale_features_to_pi(X: np.ndarray) -> np.ndarray:
    """Scale feature array to [0, π] using MinMaxScaler."""
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    return scaler.fit_transform(X)


def standardize_features(X: np.ndarray) -> tuple:
    """Standardize features with StandardScaler. Returns (X_scaled, scaler)."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler


def select_top_variance_features(df: pd.DataFrame, feature_cols: list, n: int = 4) -> list:
    """Select top-n features by variance (unsupervised, no label use)."""
    variances = df[feature_cols].var().sort_values(ascending=False)
    selected = variances.head(n).index.tolist()
    print(f"Selected top-{n} variance features: {selected}")
    return selected


def get_deterministic_sample(df: pd.DataFrame, n: int, seed: int = 42) -> tuple:
    """Return a deterministic sample index and DataFrame."""
    rng = np.random.RandomState(seed)
    idx = rng.choice(len(df), size=n, replace=False)
    idx_sorted = np.sort(idx)
    return idx_sorted, df.iloc[idx_sorted].reset_index(drop=True)
