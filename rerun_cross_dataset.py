import sys
import numpy as np
import pandas as pd
from sklearn.datasets import load_wine
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import rbf_kernel
sys.path.insert(0, '.')
from src.data import scale_features_to_pi, get_deterministic_sample
from src.quantum import build_zz_feature_map, build_quantum_kernel, compute_kernel_matrix
from src.metrics import centered_kernel_alignment, get_classical_neighbors, get_quantum_neighbors, jaccard_per_point, top_k_overlap, anomaly_category_labels
from src.classical import run_isolation_forest
from src.interestingness import quantum_anomaly_score

print("Running corrected sklearn Wine cross-dataset experiment...")
bunch = load_wine()
df_wine2 = pd.DataFrame(bunch.data, columns=bunch.feature_names)

# FIX: Standardize first
df_wine2_std = pd.DataFrame(StandardScaler().fit_transform(df_wine2), columns=bunch.feature_names)
variances = df_wine2_std.var().sort_values(ascending=False)
top4_feat = variances.head(4).index.tolist()
print(f"Corrected top-4 features: {top4_feat}")

X2 = df_wine2[top4_feat].values
idx2, df_sample2 = get_deterministic_sample(pd.DataFrame(X2), 150, seed=42)
X2_sub = df_sample2.values

X2_std = StandardScaler().fit_transform(X2_sub)
X2_scaled = scale_features_to_pi(X2_sub)

# Recompute Classical Kernel
K_c2 = rbf_kernel(X2_std, gamma=1.0/4)
np.save('outputs/kernels/K_classical2.npy', K_c2)

# Recompute Quantum Kernel (takes ~45s)
fm2 = build_zz_feature_map(n_qubits=4, reps=2)
qk2 = build_quantum_kernel(fm2)
K_q2, _ = compute_kernel_matrix(qk2, X2_scaled)
np.save('outputs/kernels/K_quantum2.npy', K_q2)

# Compute metrics
cka2 = centered_kernel_alignment(K_q2, K_c2)
c_nbrs2 = get_classical_neighbors(X2_std, 10)
q_nbrs2 = get_quantum_neighbors(K_q2, 10)
jac2 = jaccard_per_point(c_nbrs2, q_nbrs2).mean()

cas2 = run_isolation_forest(X2_std, random_state=42)
qas2 = quantum_anomaly_score(K_q2)
ov10_2 = top_k_overlap(cas2, qas2, 10)

labels2 = anomaly_category_labels(cas2, qas2, pct=90)
n_qonly2 = (labels2 == 'Quantum-only').sum()

print(f"New CKA: {cka2:.4f}, Jaccard: {jac2:.4f}, Overlap: {ov10_2:.4f}, Q-only: {n_qonly2}")

# Update cross_dataset_results.csv
df_cross = pd.read_csv('outputs/tables/cross_dataset_results.csv')
# Keep first row (Red Wine), replace second row (sklearn Wine)
red_wine_row = df_cross.iloc[0].to_dict()
new_wine_row = {
    'dataset': 'sklearn Wine', 'sample_size': 150, 'qubits': 4,
    'feature_map': 'ZZFeatureMap', 'reps': 2,
    'kernel_alignment': round(cka2, 6),
    'mean_neighborhood_jaccard': round(jac2, 4),
    'top5_anomaly_overlap': df_cross.iloc[1]['top5_anomaly_overlap'], # keep old or 0
    'top10_anomaly_overlap': round(ov10_2, 4),
    'top20_anomaly_overlap': df_cross.iloc[1]['top20_anomaly_overlap'],
    'n_quantum_only': n_qonly2
}
df_new = pd.DataFrame([red_wine_row, new_wine_row])
df_new.to_csv('outputs/tables/cross_dataset_results.csv', index=False)
print("Updated cross_dataset_results.csv")
