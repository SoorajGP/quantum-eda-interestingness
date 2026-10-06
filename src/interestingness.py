"""
src/interestingness.py — Q-Interestingness framework:
  Quantum Anomaly Score (QAS)
  Quantum Novelty (N)
  Quantum Boundary / Heterogeneity (B)
  Q-Interestingness composite score (QI)
  Weight sensitivity analysis
"""

import numpy as np
from scipy.stats import spearmanr


# ── Individual Component Scores ───────────────────────────────────────────────

def quantum_anomaly_score(K: np.ndarray) -> np.ndarray:
    """
    QAS_i = 1 - mean_{j ≠ i}(K_ij)
    Higher QAS → low average quantum similarity → exploratory candidate.
    Returns normalized scores in [0, 1].
    """
    n = K.shape[0]
    scores = np.zeros(n)
    for i in range(n):
        off_diag = np.concatenate([K[i, :i], K[i, i+1:]])
        scores[i] = 1.0 - np.mean(off_diag)
    return _normalize(scores)


def quantum_novelty(K: np.ndarray, k: int = 5) -> np.ndarray:
    """
    N_i = 1 - mean similarity to top-k quantum neighbors.
    Higher → novel in quantum feature space.
    Returns normalized scores in [0, 1].
    """
    n = K.shape[0]
    K_no_self = K.copy()
    np.fill_diagonal(K_no_self, -np.inf)
    scores = np.zeros(n)
    for i in range(n):
        top_k_idx = np.argsort(K_no_self[i])[::-1][:k]
        scores[i] = 1.0 - np.mean(K[i, top_k_idx])
    return _normalize(scores)


def quantum_boundary(K: np.ndarray) -> np.ndarray:
    """
    B_i = variance of quantum similarity values in kernel row i.
    Prototype heterogeneity measure — higher → more heterogeneous neighborhood.
    Clearly a prototype metric; not theoretically proven.
    Returns normalized scores in [0, 1].
    """
    scores = np.var(K, axis=1)
    return _normalize(scores)


# ── Q-Interestingness Composite ───────────────────────────────────────────────

def q_interestingness(
    QAS: np.ndarray,
    CAS: np.ndarray,
    N: np.ndarray,
    B: np.ndarray,
    weights: tuple = (0.40, 0.20, 0.20, 0.20),
) -> np.ndarray:
    """
    QI(x) = wq*QAS(x) + wc*CAS(x) + wn*N(x) + wb*B(x)
    All inputs assumed normalized to [0, 1].
    """
    wq, wc, wn, wb = weights
    assert abs(wq + wc + wn + wb - 1.0) < 1e-6, "Weights must sum to 1."
    QI = wq * QAS + wc * CAS + wn * N + wb * B
    return _normalize(QI)


# ── Weight Sensitivity Analysis ───────────────────────────────────────────────

WEIGHT_CONFIGS = {
    "quantum_heavy":   (0.60, 0.10, 0.20, 0.10),
    "balanced":        (0.40, 0.20, 0.20, 0.20),
    "classical_heavy": (0.20, 0.50, 0.15, 0.15),
}


def weight_sensitivity_analysis(
    QAS: np.ndarray,
    CAS: np.ndarray,
    N: np.ndarray,
    B: np.ndarray,
    configs: dict = None,
) -> dict:
    """
    Compute QI rankings for each weight configuration.
    Returns dict with rankings and Spearman correlation matrix.
    """
    if configs is None:
        configs = WEIGHT_CONFIGS

    rankings = {}
    qi_scores = {}
    for name, w in configs.items():
        qi = q_interestingness(QAS, CAS, N, B, weights=w)
        qi_scores[name] = qi
        rankings[name] = np.argsort(qi)[::-1]  # highest QI first

    # Spearman rank correlation between all config pairs
    config_names = list(configs.keys())
    n_configs = len(config_names)
    corr_matrix = np.ones((n_configs, n_configs))
    for i in range(n_configs):
        for j in range(i + 1, n_configs):
            rho, _ = spearmanr(qi_scores[config_names[i]], qi_scores[config_names[j]])
            corr_matrix[i, j] = rho
            corr_matrix[j, i] = rho

    print("\n-- Q-Interestingness Weight Sensitivity --")
    for name, w in configs.items():
        print(f"  {name}: wq={w[0]}, wc={w[1]}, wn={w[2]}, wb={w[3]}")
    print("\nSpearman rank correlation matrix:")
    for i, n in enumerate(config_names):
        row = "  " + n + ": " + "  ".join(f"{corr_matrix[i,j]:.4f}"
                                           for j in range(n_configs))
        print(row)

    return {
        "qi_scores": qi_scores,
        "rankings": rankings,
        "config_names": config_names,
        "spearman_matrix": corr_matrix,
    }


# ── Internal Helper ───────────────────────────────────────────────────────────

def _normalize(x: np.ndarray) -> np.ndarray:
    """Normalize array to [0, 1]."""
    mn, mx = x.min(), x.max()
    if mx > mn:
        return (x - mn) / (mx - mn)
    return np.zeros_like(x, dtype=float)
