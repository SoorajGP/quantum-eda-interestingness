"""
src/metrics.py — Kernel analysis, neighborhood, and anomaly-overlap metrics.
"""

import numpy as np
from scipy.stats import spearmanr


# -- Kernel Sanity Checks ------------------------------------------------------

def kernel_sanity_check(K: np.ndarray, name: str = "K") -> dict:
    """
    Run basic sanity checks on a kernel matrix.
    Returns a dict of results.
    """
    n = K.shape[0]
    assert K.shape == (n, n), f"{name}: non-square shape {K.shape}"

    sym_error = np.max(np.abs(K - K.T))
    diag_mean = np.mean(np.diag(K))
    diag_min = np.min(np.diag(K))
    nan_count = int(np.sum(np.isnan(K)))
    inf_count = int(np.sum(np.isinf(K)))
    eigenvalues = np.linalg.eigvalsh(K)
    min_eigenvalue = float(eigenvalues.min())
    is_psd = min_eigenvalue >= -1e-6

    results = {
        "name": name,
        "shape": K.shape,
        "symmetry_error": float(sym_error),
        "diagonal_mean": float(diag_mean),
        "diagonal_min": float(diag_min),
        "nan_count": nan_count,
        "inf_count": inf_count,
        "min_eigenvalue": min_eigenvalue,
        "is_psd": is_psd,
        "kernel_mean": float(np.mean(K)),
        "kernel_std": float(np.std(K)),
    }

    print(f"\n-- Sanity Check: {name} --")
    for k, v in results.items():
        print(f"  {k}: {v}")
    return results


# -- Centered Kernel Alignment ------------------------------------------------─

def center_kernel(K: np.ndarray) -> np.ndarray:
    """Return HKH where H = I - 11^T/n."""
    n = K.shape[0]
    ones = np.ones((n, n)) / n
    H = np.eye(n) - ones
    return H @ K @ H


def centered_kernel_alignment(K1: np.ndarray, K2: np.ndarray) -> float:
    """
    Centered Kernel Alignment (CKA) between two kernel matrices.
    A(K1,K2) = <K1c,K2c>_F / (||K1c||_F ||K2c||_F)
    """
    K1c = center_kernel(K1)
    K2c = center_kernel(K2)
    numerator = np.sum(K1c * K2c)
    denom = np.sqrt(np.sum(K1c ** 2) * np.sum(K2c ** 2))
    if denom < 1e-12:
        return 0.0
    return float(numerator / denom)


# -- Top-k Anomaly Overlap ----------------------------------------------------─

def top_k_overlap(scores1: np.ndarray, scores2: np.ndarray, k: int) -> float:
    """
    Proportion of top-k anomalies shared between two scoring methods.
    Overlap = |top_k(s1) ∩ top_k(s2)| / k
    """
    top1 = set(np.argsort(scores1)[::-1][:k])
    top2 = set(np.argsort(scores2)[::-1][:k])
    return len(top1 & top2) / k


def anomaly_category_labels(classical: np.ndarray, quantum: np.ndarray,
                              pct: float = 90) -> np.ndarray:
    """
    Classify observations into 4 categories using percentile thresholds.
    Returns array of strings: 'Both', 'Classical-only', 'Quantum-only', 'Neither'
    """
    c_thresh = np.percentile(classical, pct)
    q_thresh = np.percentile(quantum, pct)
    labels = []
    for c, q in zip(classical, quantum):
        if c >= c_thresh and q >= q_thresh:
            labels.append("Both")
        elif c >= c_thresh:
            labels.append("Classical-only")
        elif q >= q_thresh:
            labels.append("Quantum-only")
        else:
            labels.append("Neither")
    return np.array(labels)


# -- Neighborhood Jaccard Overlap ----------------------------------------------

def get_classical_neighbors(X: np.ndarray, k: int) -> np.ndarray:
    """
    Return (n, k) array of neighbor indices using Euclidean distance.
    Self-excluded.
    """
    from scipy.spatial.distance import cdist
    D = cdist(X, X, metric="euclidean")
    np.fill_diagonal(D, np.inf)
    neighbors = np.argsort(D, axis=1)[:, :k]
    return neighbors


def get_quantum_neighbors(K: np.ndarray, k: int) -> np.ndarray:
    """
    Return (n, k) array of neighbor indices using quantum kernel similarity.
    Self-excluded. Higher K_ij → more similar → closer neighbor.
    """
    K_no_self = K.copy()
    np.fill_diagonal(K_no_self, -np.inf)
    neighbors = np.argsort(K_no_self, axis=1)[:, ::-1][:, :k]
    return neighbors


def jaccard_per_point(classical_nbrs: np.ndarray, quantum_nbrs: np.ndarray) -> np.ndarray:
    """
    Compute per-point Jaccard overlap between classical and quantum neighborhoods.
    J(A,B) = |A∩B| / |A∪B|
    """
    n = classical_nbrs.shape[0]
    scores = np.zeros(n)
    for i in range(n):
        A = set(classical_nbrs[i])
        B = set(quantum_nbrs[i])
        intersection = len(A & B)
        union = len(A | B)
        scores[i] = intersection / union if union > 0 else 0.0
    return scores


def neighborhood_jaccard_summary(X: np.ndarray, K: np.ndarray, k_values=(5, 10, 15)) -> dict:
    """
    Calculate Jaccard neighborhood overlap for multiple k values.
    Returns dict of {k: {'mean', 'median', 'std', 'per_point'}}.
    """
    results = {}
    for k in k_values:
        c_nbrs = get_classical_neighbors(X, k)
        q_nbrs = get_quantum_neighbors(K, k)
        j = jaccard_per_point(c_nbrs, q_nbrs)
        results[k] = {
            "mean": float(np.mean(j)),
            "median": float(np.median(j)),
            "std": float(np.std(j)),
            "per_point": j,
        }
        print(f"  Jaccard k={k}: mean={np.mean(j):.4f}, median={np.median(j):.4f}, "
              f"std={np.std(j):.4f}")
    return results
