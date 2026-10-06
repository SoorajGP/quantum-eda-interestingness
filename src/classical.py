"""
src/classical.py — Classical EDA, kernel, and anomaly-detection utilities.
"""

import numpy as np
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import warnings


def compute_classical_kernel(X: np.ndarray, gamma: float = None) -> np.ndarray:
    """Compute RBF kernel matrix. gamma default → 1/n_features."""
    if gamma is None:
        gamma = 1.0 / X.shape[1]
    K = rbf_kernel(X, gamma=gamma)
    return K.astype(np.float64)


def run_isolation_forest(X: np.ndarray, contamination: float = 0.1,
                          random_state: int = 42) -> np.ndarray:
    """
    Run IsolationForest and return normalized anomaly scores in [0, 1].
    Higher score → more anomalous.
    """
    clf = IsolationForest(contamination=contamination, random_state=random_state)
    clf.fit(X)
    raw = clf.decision_function(X)   # higher → more normal
    scores = -raw                    # flip so higher → more anomalous
    # Normalize to [0, 1]
    mn, mx = scores.min(), scores.max()
    if mx > mn:
        scores = (scores - mn) / (mx - mn)
    else:
        scores = np.zeros_like(scores)
    return scores


def run_lof(X: np.ndarray, n_neighbors: int = 20, contamination: float = 0.1) -> np.ndarray:
    """
    Run LocalOutlierFactor and return normalized anomaly scores in [0, 1].
    Higher score → more anomalous.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
        clf.fit_predict(X)
        raw = clf.negative_outlier_factor_   # more negative → more anomalous
    scores = -raw
    mn, mx = scores.min(), scores.max()
    if mx > mn:
        scores = (scores - mn) / (mx - mn)
    else:
        scores = np.zeros_like(scores)
    return scores


def run_pca(X: np.ndarray, n_components: int = 2) -> tuple:
    """Run PCA and return (embedding, explained_variance_ratio)."""
    pca = PCA(n_components=n_components, random_state=42)
    embedding = pca.fit_transform(X)
    return embedding, pca.explained_variance_ratio_


def run_umap(X: np.ndarray, n_components: int = 2, n_neighbors: int = 15,
             random_state: int = 42) -> np.ndarray:
    """Run UMAP and return 2D embedding."""
    import umap as umap_module
    reducer = umap_module.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        random_state=random_state,
    )
    return reducer.fit_transform(X)


def run_kernel_pca(K: np.ndarray, n_components: int = 2) -> np.ndarray:
    """Run KernelPCA with precomputed kernel."""
    from sklearn.decomposition import KernelPCA
    kpca = KernelPCA(n_components=n_components, kernel="precomputed")
    return kpca.fit_transform(K)
