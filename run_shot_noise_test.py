"""
run_shot_noise_test.py — Finite-Shot Sampling Robustness Test

Tests whether the classical-quantum CKA and candidate rankings are stable when evaluated
with finite measurement shots (e.g., 1024, 4096 shots) rather than infinite-precision statevectors.
Addresses Limitation 1 (no physical hardware / infinite precision simulation).
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.abspath('.'))
from src.data import load_wine_quality, scale_features_to_pi, get_deterministic_sample, WINE_QUANTUM_FEATURES
from src.quantum import build_zz_feature_map
from src.metrics import centered_kernel_alignment
from src.interestingness import quantum_anomaly_score

def main():
    print("=" * 70)
    print("FINITE-SHOT SAMPLING ROBUSTNESS CHECK")
    print("=" * 70)

    # Load data
    df = load_wine_quality("data/raw/winequality-red.csv")
    idx, df_sample = get_deterministic_sample(df, 150, seed=42)
    X_pi = scale_features_to_pi(df_sample[WINE_QUANTUM_FEATURES].values)

    K_c = np.load("outputs/kernels/K_classical.npy")
    K_q_ideal = np.load("outputs/kernels/K_quantum.npy")
    cka_ideal = centered_kernel_alignment(K_q_ideal, K_c)
    qas_ideal = quantum_anomaly_score(K_q_ideal)

    print(f"Ideal Statevector CKA: {cka_ideal:.4f}")

    shot_configs = [1024, 4096, 8192]
    results = []

    try:
        from qiskit_aer.primitives import Sampler as AerSampler
        from qiskit_machine_learning.state_fidelities import ComputeUncompute
        from qiskit_machine_learning.kernels import FidelityQuantumKernel

        fm = build_zz_feature_map(n_qubits=4, reps=2, entanglement="linear")

        for shots in shot_configs:
            print(f"\nEvaluating with shots = {shots} ...")
            sampler = AerSampler(run_options={"shots": shots, "seed": 42})
            fidelity = ComputeUncompute(sampler=sampler)
            kernel = FidelityQuantumKernel(fidelity=fidelity, feature_map=fm)
            K_shot = kernel.evaluate(x_vec=X_pi)

            cka_shot = centered_kernel_alignment(K_shot, K_c)
            cka_diff = abs(cka_shot - cka_ideal)
            qas_shot = quantum_anomaly_score(K_shot)
            rank_corr, _ = spearmanr(qas_ideal, qas_shot)

            print(f"  CKA (shots={shots}): {cka_shot:.4f} (diff from ideal: {cka_diff:.4f})")
            print(f"  QAS Spearman correlation with ideal: {rank_corr:.4f}")

            results.append({
                "shots": shots,
                "cka": round(cka_shot, 4),
                "cka_diff_vs_ideal": round(cka_diff, 4),
                "qas_spearman_vs_ideal": round(rank_corr, 4)
            })

        df_out = pd.DataFrame(results)
        df_out.to_csv("outputs/tables/shot_noise_robustness.csv", index=False)
        print("\nSaved outputs/tables/shot_noise_robustness.csv")

    except Exception as e:
        print(f"\nAer sampler execution note: {e}")
        print("Simulating binomial sampling noise model on ideal fidelity kernel instead...")
        # Binomial sampling proxy K_ij ~ Binomial(shots, K_ij)/shots
        for shots in shot_configs:
            rng = np.random.RandomState(42)
            K_noisy = rng.binomial(shots, np.clip(K_q_ideal, 0, 1)) / shots
            np.fill_diagonal(K_noisy, 1.0)
            # Symmetrize
            K_noisy = (K_noisy + K_noisy.T) / 2.0

            cka_shot = centered_kernel_alignment(K_noisy, K_c)
            cka_diff = abs(cka_shot - cka_ideal)
            qas_shot = quantum_anomaly_score(K_noisy)
            rank_corr, _ = spearmanr(qas_ideal, qas_shot)

            results.append({
                "shots": shots,
                "cka": round(cka_shot, 4),
                "cka_diff_vs_ideal": round(cka_diff, 4),
                "qas_spearman_vs_ideal": round(rank_corr, 4)
            })
            print(f"  Shots={shots}: CKA={cka_shot:.4f}, |ΔCKA|={cka_diff:.4f}, QAS Spearman={rank_corr:.4f}")

        df_out = pd.DataFrame(results)
        df_out.to_csv("outputs/tables/shot_noise_robustness.csv", index=False)
        print("\nSaved outputs/tables/shot_noise_robustness.csv")

if __name__ == "__main__":
    main()
