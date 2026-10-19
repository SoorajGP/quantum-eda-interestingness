"""
run_third_dataset.py — Third Real-World Dataset Validation (Breast Cancer Wisconsin)

Tests whether the classical-quantum geometric divergence generalizes to a third distinct
tabular domain (clinical / diagnostic data), addressing Limitation 8 of the research audit.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import rbf_kernel

sys.path.insert(0, os.path.abspath('.'))
from src.data import scale_features_to_pi, get_deterministic_sample
from src.quantum import build_zz_feature_map, build_quantum_kernel, compute_kernel_matrix
from src.metrics import (
    centered_kernel_alignment,
    get_classical_neighbors,
    get_quantum_neighbors,
    jaccard_per_point,
    top_k_overlap,
    anomaly_category_labels
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

def main():
    print("=" * 70)
    print("CROSS-DATASET VALIDATION: Breast Cancer Wisconsin (Diagnostic)")
    print("=" * 70)

    # 1. Load data
    bunch = load_breast_cancer()
    df_raw = pd.DataFrame(bunch.data, columns=bunch.feature_names)
    print(f"Loaded dataset: {df_raw.shape[0]} samples, {df_raw.shape[1]} features")

    # 2. Standardize features first, pick top-4 highest variance features
    scaler = StandardScaler()
    df_std = pd.DataFrame(scaler.fit_transform(df_raw), columns=bunch.feature_names)
    top4_cols = df_std.var().sort_values(ascending=False).head(4).index.tolist()
    print(f"Top 4 variance features: {top4_cols}")

    # 3. Deterministic sample of N=150
    X_top4 = df_raw[top4_cols].values
    idx, df_sample = get_deterministic_sample(pd.DataFrame(X_top4), 150, seed=42)
    X_sub = df_sample.values

    X_std = scaler.fit_transform(X_sub)
    X_scaled = scale_features_to_pi(X_sub)

    # 4. Classical and Quantum Kernels
    K_c = rbf_kernel(X_std, gamma=1.0 / 4)
    fm = build_zz_feature_map(n_qubits=4, reps=2, entanglement="linear")
    qk = build_quantum_kernel(fm)
    K_q, runtime_s = compute_kernel_matrix(qk, X_scaled)

    # 5. Metrics
    cka = centered_kernel_alignment(K_q, K_c)
    divergence_D = 1.0 - cka

    c_nbrs = get_classical_neighbors(X_std, 10)
    q_nbrs = get_quantum_neighbors(K_q, 10)
    jac10 = float(jaccard_per_point(c_nbrs, q_nbrs).mean())

    cas = run_isolation_forest(X_std, random_state=42)
    qas = quantum_anomaly_score(K_q)
    nov = quantum_novelty(K_q, k=5)
    het = quantum_neighborhood_heterogeneity(K_q)

    qu = quantum_unusualness(qas, nov, het)
    c_nbrs5 = get_classical_neighbors(X_std, 5)
    q_nbrs5 = get_quantum_neighbors(K_q, 5)
    j5 = jaccard_per_point(c_nbrs5, q_nbrs5)
    rd = representation_disagreement(qas, cas, j5)
    qi_v2 = q_interestingness_v2(qu, rd, lam=0.5)

    ov5 = top_k_overlap(cas, qas, 5)
    ov10 = top_k_overlap(cas, qas, 10)
    ov20 = top_k_overlap(cas, qas, 20)

    labels = anomaly_category_labels(cas, qas, pct=90)
    n_qonly = int((labels == "Quantum-only").sum())

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY:")
    print(f"  Classical-Quantum CKA:              {cka:.4f}  (Divergence D = {divergence_D:.4f})")
    print(f"  Neighborhood Jaccard @ 10:          {jac10:.4f}")
    print(f"  Top-10 Anomaly Overlap:             {ov10:.4f}")
    print(f"  Quantum-Specific Candidates:        {n_qonly} / 150")
    print(f"  Evaluation Runtime:                 {runtime_s:.1f}s")
    print("=" * 70)

    # 6. Append to cross_dataset_results.csv
    table_path = "outputs/tables/cross_dataset_results.csv"
    if os.path.exists(table_path):
        df_cross = pd.read_csv(table_path)
        # Check if already present
        df_cross = df_cross[df_cross["dataset"] != "Breast Cancer Wisconsin"]
        new_row = {
            "dataset": "Breast Cancer Wisconsin",
            "sample_size": 150,
            "qubits": 4,
            "feature_map": "ZZFeatureMap",
            "reps": 2,
            "kernel_alignment": round(cka, 6),
            "mean_neighborhood_jaccard": round(jac10, 4),
            "top5_anomaly_overlap": round(ov5, 4),
            "top10_anomaly_overlap": round(ov10, 4),
            "top20_anomaly_overlap": round(ov20, 4),
            "n_quantum_only": n_qonly
        }
        df_cross = pd.concat([df_cross, pd.DataFrame([new_row])], ignore_index=True)
        df_cross.to_csv(table_path, index=False)
        print(f"Updated {table_path} with 3rd dataset!")

if __name__ == "__main__":
    main()
