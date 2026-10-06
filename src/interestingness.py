"""
src/interestingness.py — Q-Interestingness framework:
  Quantum Anomaly Score (QAS)
  Quantum Novelty (N)
  Quantum Neighborhood Heterogeneity (B)
  Quantum Unusualness (QU)
  Representation Disagreement (RD)
  Q-Interestingness (QI_v2)
"""

import numpy as np
from scipy.stats import spearmanr

def _normalize(x: np.ndarray) -> np.ndarray:
    """Normalize array to [0, 1]."""
    mn, mx = np.nanmin(x), np.nanmax(x)
    if mx > mn:
        return (x - mn) / (mx - mn)
    return np.zeros_like(x, dtype=float)

# ── Individual Component Scores ───────────────────────────────────────────────

def quantum_anomaly_score(K: np.ndarray) -> np.ndarray:
    """QAS_i = 1 - mean_{j ≠ i}(K_ij). Normalized to [0,1]."""
    n = K.shape[0]
    scores = np.zeros(n)
    for i in range(n):
        off_diag = np.concatenate([K[i, :i], K[i, i+1:]])
        scores[i] = 1.0 - np.mean(off_diag)
    return _normalize(scores)

def quantum_novelty(K: np.ndarray, k: int = 5) -> np.ndarray:
    """N_i = 1 - mean similarity to top-k quantum neighbors. Normalized to [0,1]."""
    n = K.shape[0]
    K_no_self = K.copy().astype(float)
    np.fill_diagonal(K_no_self, -np.inf)
    scores = np.zeros(n)
    for i in range(n):
        top_k_idx = np.argsort(K_no_self[i])[::-1][:k]
        scores[i] = 1.0 - np.mean(K[i, top_k_idx])
    return _normalize(scores)

def quantum_neighborhood_heterogeneity(K: np.ndarray) -> np.ndarray:
    """
    B_i = nanvar(K[i, j≠i]).
    Excludes diagonal self-similarity. Higher -> more heterogeneous neighborhood.
    Normalized to [0, 1].
    """
    K_no_self = K.copy().astype(float)
    np.fill_diagonal(K_no_self, np.nan)
    scores = np.nanvar(K_no_self, axis=1)
    return _normalize(scores)

def quantum_local_global_contrast(K: np.ndarray, k: int = 5) -> np.ndarray:
    """
    QLGC_i = mean_near_i - mean_global_i.
    Diagnostic metric; NOT automatically included in QI.
    Returns raw unnormalized values.
    """
    n = K.shape[0]
    K_ns = K.copy().astype(float)
    np.fill_diagonal(K_ns, -np.inf)
    qlgc = np.zeros(n)
    for i in range(n):
        top_k = np.argsort(K_ns[i])[::-1][:k]
        mean_near = np.mean(K[i, top_k])
        off_diag  = np.concatenate([K[i, :i], K[i, i+1:]])
        mean_global = np.mean(off_diag)
        qlgc[i] = mean_near - mean_global
    return qlgc

# ── Q-Interestingness V2 Framework ────────────────────────────────────────────

def quantum_unusualness(QAS: np.ndarray, N: np.ndarray, B: np.ndarray, w=(0.5, 0.3, 0.2)) -> np.ndarray:
    """QU = w1*QAS + w2*N + w3*B. Measures point unusualness inside quantum feature space."""
    wu, wn, wb = w
    assert abs(wu+wn+wb - 1.0) < 1e-6, "Weights must sum to 1."
    return _normalize(wu * QAS + wn * N + wb * B)

def representation_disagreement(QAS: np.ndarray, CAS: np.ndarray, J: np.ndarray, w=(0.5, 0.5)) -> np.ndarray:
    """RD = w1*|QAS-CAS| + w2*(1-J). Measures representation divergence."""
    wa, wj = w
    assert abs(wa+wj - 1.0) < 1e-6, "Weights must sum to 1."
    return _normalize(wa * np.abs(QAS - CAS) + wj * (1.0 - J))

def q_interestingness_v2(QU: np.ndarray, RD: np.ndarray, lam: float = 0.5) -> np.ndarray:
    """QI_v2 = lambda * QU + (1 - lambda) * RD."""
    return _normalize(lam * QU + (1.0 - lam) * RD)

def weight_sensitivity_analysis(QU: np.ndarray, RD: np.ndarray, lambdas: list = None) -> dict:
    """Compute QI rankings for various lambda weightings."""
    if lambdas is None:
        lambdas = [0.1, 0.25, 0.5, 0.75, 0.9]
    
    qi_scores = {}
    for lam in lambdas:
        qi_scores[f"lam_{lam}"] = q_interestingness_v2(QU, RD, lam=lam)
    
    config_names = list(qi_scores.keys())
    n_configs = len(config_names)
    corr_matrix = np.ones((n_configs, n_configs))
    for i in range(n_configs):
        for j in range(i + 1, n_configs):
            rho, _ = spearmanr(qi_scores[config_names[i]], qi_scores[config_names[j]])
            corr_matrix[i, j] = rho
            corr_matrix[j, i] = rho
            
    return {
        "qi_scores": qi_scores,
        "config_names": config_names,
        "spearman_matrix": corr_matrix,
    }
