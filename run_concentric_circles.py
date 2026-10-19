"""
run_concentric_circles.py — Concentric Circles Synthetic Validation

Tests the Q-Interestingness framework on non-linearly separable nested circular manifolds
with injected spatial anomalies, characterizing how quantum phase encoding handles radial structures.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.datasets import make_circles
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import rbf_kernel

sys.path.insert(0, os.path.abspath('.'))
from src.data import scale_features_to_pi
from src.quantum import build_zz_feature_map, build_quantum_kernel, compute_kernel_matrix
from src.metrics import (
    centered_kernel_alignment,
    get_classical_neighbors,
    get_quantum_neighbors,
    jaccard_per_point
)
from src.classical import run_isolation_forest
from src.interestingness import (
    quantum_anomaly_score,
    quantum_novelty,
    quantum_neighborhood_heterogeneity,
    quantum_unusualness,
    representation_disagreement,
    q_interestingness_v2
)

def synthetic_precision_at_k(synth_scores, gt_labels, k):
    """Precision@k: proportion of injected anomalies among top-k highest scored."""
    top_k = set(np.argsort(synth_scores)[::-1][:k])
    true_anom = set(np.where(gt_labels == 1)[0])
    return len(top_k & true_anom) / k

def main():
    print("=" * 70)
    print("SYNTHETIC MANIFOLD EXPERIMENT: Concentric Circles")
    print("=" * 70)

    # 1. Generate concentric circles + 10 injected anomalies
    rng = np.random.RandomState(42)
    X_circles, y_circles = make_circles(n_samples=120, noise=0.08, factor=0.4, random_state=42)
    X_anom = rng.uniform(-2.5, 2.5, (10, 2))

    X_all = np.vstack([X_circles, X_anom])
    gt = np.array([0] * 120 + [1] * 10)

    # Pad to 4 features for 4-qubit circuit (consistent with TwoMoons in upgrade.py)
    X_all4 = np.column_stack([X_all, np.zeros((len(X_all), 2))])

    # 2. Scaling
    X_std = StandardScaler().fit_transform(X_all4)
    X_pi = scale_features_to_pi(X_all4)

    # 3. Kernel computation
    fm = build_zz_feature_map(n_qubits=4, reps=2, entanglement="linear")
    qk = build_quantum_kernel(fm)
    K_q, runtime_s = compute_kernel_matrix(qk, X_pi)
    K_c = rbf_kernel(X_std, gamma=1.0 / 4)

    # 4. Metrics & Scores
    cka = centered_kernel_alignment(K_q, K_c)
    cas = run_isolation_forest(X_std, random_state=42)
    qas = quantum_anomaly_score(K_q)
    nov = quantum_novelty(K_q, k=5)
    het = quantum_neighborhood_heterogeneity(K_q)

    c_nbrs = get_classical_neighbors(X_std, 5)
    q_nbrs = get_quantum_neighbors(K_q, 5)
    j5 = jaccard_per_point(c_nbrs, q_nbrs)

    qu = quantum_unusualness(qas, nov, het)
    rd = representation_disagreement(qas, cas, j5)
    qi = q_interestingness_v2(qu, rd, lam=0.5)

    res = {
        "dataset": "ConcentricCircles+InjectedAnomalies",
        "n_obs": len(X_all),
        "n_anomalies": int(gt.sum()),
        "cka": round(cka, 4),
        "runtime_s": round(runtime_s, 1)
    }

    scorers = [("CAS", cas), ("QAS", qas), ("QU", qu), ("RD", rd), ("QI", qi)]
    for name, s in scorers:
        for k in [5, 10, 20]:
            res[f"{name}_P@{k}"] = round(synthetic_precision_at_k(s, gt, k), 4)

    print("\n" + "=" * 70)
    print("PRECISION@k PERFORMANCE:")
    print(f"  Classical-Quantum CKA: {cka:.4f}")
    print(f"  Isolation Forest (CAS): P@5={res['CAS_P@5']}, P@10={res['CAS_P@10']}, P@20={res['CAS_P@20']}")
    print(f"  Quantum Anomaly (QAS):  P@5={res['QAS_P@5']}, P@10={res['QAS_P@10']}, P@20={res['QAS_P@20']}")
    print(f"  Quantum Unusualness(QU):P@5={res['QU_P@5']}, P@10={res['QU_P@10']}, P@20={res['QU_P@20']}")
    print(f"  Representation Dis.(RD):P@5={res['RD_P@5']}, P@10={res['RD_P@10']}, P@20={res['RD_P@20']}")
    print(f"  Composite QI_v2:        P@5={res['QI_P@5']}, P@10={res['QI_P@10']}, P@20={res['QI_P@20']}")
    print("=" * 70)

    # 5. Append to synthetic_validation.csv
    table_path = "outputs/tables/synthetic_validation.csv"
    if os.path.exists(table_path):
        synth_df = pd.read_csv(table_path)
        synth_df = synth_df[synth_df["dataset"] != "ConcentricCircles+InjectedAnomalies"]
        synth_df = pd.concat([synth_df, pd.DataFrame([res])], ignore_index=True)
        synth_df.to_csv(table_path, index=False)
        print(f"Updated {table_path} with concentric circles results!")

if __name__ == "__main__":
    main()
