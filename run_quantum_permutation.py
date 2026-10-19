"""
run_quantum_permutation.py — Full Quantum Permutation Test (B=100)

Evaluates the formal statistical significance of the classical-quantum CKA divergence
by permuting feature columns across observations and recomputing true quantum kernels.
Supports incremental saving and resumption.
"""

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.abspath('.'))
from src.data import load_wine_quality, scale_features_to_pi, get_deterministic_sample, WINE_QUANTUM_FEATURES
from src.quantum import build_zz_feature_map, build_quantum_kernel, compute_kernel_matrix
from src.metrics import centered_kernel_alignment

def main():
    parser = argparse.ArgumentParser(description="Run Full Quantum Permutation Test")
    parser.add_argument("--permutations", "-B", type=int, default=100, help="Number of permutations (default: 100)")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from previous progress if exists")
    args = parser.parse_args()

    B_TARGET = args.permutations
    OUTPUT_CSV = "outputs/tables/quantum_permutation_progress.csv"
    SUMMARY_CSV = "outputs/tables/permutation_control_upgraded.csv"
    os.makedirs("outputs/tables", exist_ok=True)

    print("=" * 70)
    print(f"FULL QUANTUM PERMUTATION TEST (Target B = {B_TARGET})")
    print("=" * 70)

    # 1. Load data and reference kernels
    df = load_wine_quality("data/raw/winequality-red.csv")
    idx, df_sample = get_deterministic_sample(df, 150, seed=42)
    X_raw = df_sample[WINE_QUANTUM_FEATURES].values

    K_c = np.load("outputs/kernels/K_classical.npy")
    K_q_obs = np.load("outputs/kernels/K_quantum.npy")
    observed_cka = centered_kernel_alignment(K_q_obs, K_c)
    print(f"Observed CKA (classical-quantum): {observed_cka:.4f}")

    # 2. Check existing progress
    completed_ckas = []
    start_b = 0
    if args.resume and os.path.exists(OUTPUT_CSV):
        prog_df = pd.read_csv(OUTPUT_CSV)
        completed_ckas = prog_df["permutation_cka"].tolist()
        start_b = len(completed_ckas)
        print(f"Resuming from iteration {start_b}/{B_TARGET} (found {len(completed_ckas)} prior runs)")

    if start_b >= B_TARGET:
        print(f"Target of {B_TARGET} permutations already reached.")
    else:
        # Pre-build quantum kernel evaluator
        fm = build_zz_feature_map(n_qubits=4, reps=2, entanglement="linear")
        qk = build_quantum_kernel(fm)

        t_start = time.time()
        for b in range(start_b, B_TARGET):
            t0 = time.time()
            rng = np.random.RandomState(seed=1000 + b)
            # Permute each feature column independently
            X_perm = X_raw.copy()
            for col in range(X_perm.shape[1]):
                X_perm[:, col] = rng.permutation(X_perm[:, col])

            X_perm_scaled = scale_features_to_pi(X_perm)
            K_q_perm, _ = compute_kernel_matrix(qk, X_perm_scaled)
            cka_perm = centered_kernel_alignment(K_q_perm, K_c)
            completed_ckas.append(cka_perm)
            elapsed = time.time() - t0

            # Save progress immediately
            df_progress = pd.DataFrame({
                "iteration": list(range(1, len(completed_ckas) + 1)),
                "permutation_cka": completed_ckas
            })
            df_progress.to_csv(OUTPUT_CSV, index=False)

            total_elapsed = time.time() - t_start
            avg_per_iter = total_elapsed / (b - start_b + 1)
            remaining = avg_per_iter * (B_TARGET - b - 1)
            print(f"  [{b+1}/{B_TARGET}] CKA_null = {cka_perm:.4f} (took {elapsed:.1f}s, est. remaining: {remaining/60:.1f} min)")

    # 3. Compute final statistical summary
    null_arr = np.array(completed_ckas[:B_TARGET])
    null_mean = float(np.mean(null_arr))
    null_std = float(np.std(null_arr))
    z_score = float((observed_cka - null_mean) / null_std) if null_std > 0 else np.nan
    # Empirical p-value (upper tail): proportion of null CKAs >= observed_cka
    # Testing whether observed structured alignment exceeds random feature shuffling
    p_val = float((1 + np.sum(null_arr >= observed_cka)) / (len(null_arr) + 1))

    print("\n" + "=" * 70)
    print("FINAL QUANTUM PERMUTATION RESULTS:")
    print(f"  Permutations (B):      {len(null_arr)}")
    print(f"  Observed CKA:          {observed_cka:.4f}")
    print(f"  Null Mean CKA:         {null_mean:.4f}")
    print(f"  Null Std CKA:          {null_std:.4f}")
    print(f"  Standardized z-score:  {z_score:.2f}")
    print(f"  Empirical p-value:     {p_val:.4f} (p < {p_val:.2f})")
    print("=" * 70)

    # Update summary table cleanly avoiding pandas dtype conversion issues
    if os.path.exists(SUMMARY_CSV):
        sum_df = pd.read_csv(SUMMARY_CSV, dtype=str)
        mask = sum_df["test"] == "full_quantum_perm_100"
        if mask.any():
            sum_df.loc[mask, "B"] = str(len(null_arr))
            sum_df.loc[mask, "null_mean"] = f"{null_mean:.4f}"
            sum_df.loc[mask, "null_std"] = f"{null_std:.4f}"
            sum_df.loc[mask, "observed_cka"] = f"{observed_cka:.4f}"
            sum_df.loc[mask, "z_score"] = f"{z_score:.4f}"
            sum_df.loc[mask, "empirical_p"] = f"{p_val:.4f}"
            sum_df.loc[mask, "status"] = "COMPLETED"
            sum_df.to_csv(SUMMARY_CSV, index=False)
            print(f"Updated {SUMMARY_CSV}")

if __name__ == "__main__":
    main()
