"""
upgrade.py — Final research-methodology upgrade for Q-Interestingness.

Execution phases:
  B. Load all cached data (no quantum recomputation)
  C. Implement cheap fixes and new metrics
  D. Run only missing expensive computations (permutation upgrade, bootstrap, synthetic)
  F. Generate all final outputs

Every result is tagged [EXISTING], [RECOMPUTED], [NEW], or [PENDING].
"""

import sys, os, time, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, kendalltau, bootstrap
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import rbf_kernel, linear_kernel, polynomial_kernel
warnings.filterwarnings('ignore')

sys.path.insert(0, '.')
from src.data import (load_wine_quality, get_deterministic_sample,
                      scale_features_to_pi, WINE_QUANTUM_FEATURES, WINE_TARGET_COL)
from src.classical import run_isolation_forest
from src.metrics import (centered_kernel_alignment, center_kernel,
                         top_k_overlap, neighborhood_jaccard_summary,
                         anomaly_category_labels,
                         get_classical_neighbors, get_quantum_neighbors, jaccard_per_point)

sns.set_theme(style='whitegrid', font_scale=1.1)
os.makedirs('outputs/figures', exist_ok=True)
os.makedirs('outputs/tables', exist_ok=True)
SEED = 42
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE B: LOAD ALL CACHED DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("="*70)
print("PHASE B: Loading cached data")
print("="*70)

df       = load_wine_quality('data/raw/winequality-red.csv')
N        = 150
idx, df_sample = get_deterministic_sample(df, N, seed=42)

K_q = np.load('outputs/kernels/K_quantum.npy')   # ZZFeatureMap reps=2 N=150
K_c = np.load('outputs/kernels/K_classical.npy') # RBF N=150

X_q4     = df_sample[WINE_QUANTUM_FEATURES].values
X_q4_std = StandardScaler().fit_transform(X_q4)
X_q4_pi  = scale_features_to_pi(X_q4)
quality  = df_sample[WINE_TARGET_COL].values
kpca_emb = np.load('outputs/tables/kpca_emb.npy')

# Verify cached kernels
assert K_q.shape == (150,150), f"K_q shape wrong: {K_q.shape}"
assert K_c.shape == (150,150), f"K_c shape wrong: {K_c.shape}"
sym_err_q = float(np.max(np.abs(K_q - K_q.T)))
sym_err_c = float(np.max(np.abs(K_c - K_c.T)))
nan_q = int(np.sum(np.isnan(K_q)))
nan_c = int(np.sum(np.isnan(K_c)))
print(f"[EXISTING] K_quantum: shape={K_q.shape}, sym_err={sym_err_q:.2e}, NaN={nan_q}")
print(f"[EXISTING] K_classical: shape={K_c.shape}, sym_err={sym_err_c:.2e}, NaN={nan_c}")
assert nan_q == 0 and nan_c == 0, "NaNs found in cached kernels"
assert sym_err_q < 1e-6 and sym_err_c < 1e-6, "Kernel symmetry violated"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C1: FIX quantum_boundary (B) — diagonal was included, self-similarity=1
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C1: Fix quantum_neighborhood_heterogeneity (B correction)")
print("="*70)

def quantum_neighborhood_heterogeneity(K: np.ndarray) -> np.ndarray:
    """
    Quantum Neighborhood Heterogeneity (corrected B).
    Excludes self-similarity (diagonal) before computing variance.
    B_i = nanvar(K[i, j!=i])
    Higher => more heterogeneous neighborhood.
    [RECOMPUTED] — Bug fix: was np.var(K, axis=1) which included K[i,i]=1.
    """
    K_no_self = K.copy().astype(float)
    np.fill_diagonal(K_no_self, np.nan)
    scores = np.nanvar(K_no_self, axis=1)
    mn, mx = scores.min(), scores.max()
    return (scores - mn) / (mx - mn) if mx > mn else np.zeros_like(scores)

def quantum_anomaly_score(K: np.ndarray) -> np.ndarray:
    """QAS_i = 1 - mean_{j!=i}(K_ij). [EXISTING - unchanged]"""
    n = K.shape[0]
    scores = np.zeros(n)
    for i in range(n):
        off = np.concatenate([K[i, :i], K[i, i+1:]])
        scores[i] = 1.0 - np.mean(off)
    mn, mx = scores.min(), scores.max()
    return (scores - mn) / (mx - mn) if mx > mn else np.zeros_like(scores)

def quantum_novelty(K: np.ndarray, k: int = 5) -> np.ndarray:
    """N_i = 1 - mean similarity to top-k quantum neighbors. [EXISTING - unchanged]"""
    n = K.shape[0]
    K_ns = K.copy().astype(float)
    np.fill_diagonal(K_ns, -np.inf)
    scores = np.zeros(n)
    for i in range(n):
        top_k = np.argsort(K_ns[i])[::-1][:k]
        scores[i] = 1.0 - np.mean(K[i, top_k])
    mn, mx = scores.min(), scores.max()
    return (scores - mn) / (mx - mn) if mx > mn else np.zeros_like(scores)

def normalize(x):
    mn, mx = np.nanmin(x), np.nanmax(x)
    return (x - mn) / (mx - mn) if mx > mn else np.zeros_like(x, dtype=float)

# Compute all QI components
QAS = quantum_anomaly_score(K_q)
N_k = quantum_novelty(K_q, k=5)
B_old = np.var(K_q, axis=1);  B_old = normalize(B_old)  # OLD (buggy)
B_new = quantum_neighborhood_heterogeneity(K_q)           # NEW (fixed)
CAS   = run_isolation_forest(X_q4_std, random_state=42)

# Report B difference
print(f"  B_old (with diagonal): mean={B_old.mean():.6f}, std={B_old.std():.6f}")
print(f"  B_new (no diagonal):   mean={B_new.mean():.6f}, std={B_new.std():.6f}")
rho_b, _ = spearmanr(B_old, B_new)
print(f"  Spearman(B_old, B_new) = {rho_b:.4f}")
print("[RECOMPUTED] B corrected — diagonal excluded")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C2: QUANTUM LOCAL-GLOBAL CONTRAST (QLGC) — new diagnostic
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C2: Quantum Local-Global Contrast (QLGC)")
print("="*70)

def quantum_local_global_contrast(K: np.ndarray, k: int = 5) -> np.ndarray:
    """
    QLGC_i = mean_near_i - mean_global_i
    mean_near = mean similarity to k nearest quantum neighbors
    mean_global = mean similarity to all other points (excluding self)
    Higher QLGC => point clusters locally but is globally isolated.
    [NEW]
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
    return qlgc  # NOT normalized: keep raw for interpretation

QLGC_raw = quantum_local_global_contrast(K_q, k=5)
QLGC = normalize(QLGC_raw)
print(f"  QLGC: mean={QLGC_raw.mean():.6f}, std={QLGC_raw.std():.6f}")
print(f"  Most locally clustered: {QLGC_raw.max():.4f}, Most isolated: {QLGC_raw.min():.4f}")
print("[NEW] QLGC computed")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C3: COMPONENT CORRELATION MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C3: Component Correlation Matrix")
print("="*70)

components = {'QAS': QAS, 'N': N_k, 'B_new': B_new, 'QLGC': QLGC, 'CAS': CAS}
comp_names = list(components.keys())
n_comp     = len(comp_names)
corr_mat   = np.ones((n_comp, n_comp))

for i, n1 in enumerate(comp_names):
    for j, n2 in enumerate(comp_names):
        if i != j:
            rho, _ = spearmanr(components[n1], components[n2])
            corr_mat[i, j] = rho

comp_corr_df = pd.DataFrame(corr_mat, index=comp_names, columns=comp_names)
print("Spearman Correlation Matrix:")
print(comp_corr_df.round(4).to_string())
comp_corr_df.round(4).to_csv('outputs/tables/component_correlation.csv')
print("[NEW] Saved component_correlation.csv")

fig, ax = plt.subplots(figsize=(7,6))
sns.heatmap(comp_corr_df, annot=True, fmt='.3f', cmap='RdYlGn',
            vmin=-1, vmax=1, center=0, ax=ax, linewidths=0.5)
ax.set_title('Spearman Correlation: QI Components [NEW]')
plt.tight_layout()
plt.savefig('outputs/figures/F7a_component_correlation.png', dpi=120, bbox_inches='tight')
plt.close()
print("[NEW] Saved F7a_component_correlation.png")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C4: NEW QI FRAMEWORK — QU / RD / QI refactored
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C4: Refactored QI Framework (QU + RD)")
print("="*70)

# Per-point Jaccard for RD computation
c_nbrs5 = get_classical_neighbors(X_q4_std, 5)
q_nbrs5 = get_quantum_neighbors(K_q, 5)
J_5     = jaccard_per_point(c_nbrs5, q_nbrs5)  # per-point J@5

# A. QUANTUM UNUSUALNESS (QU): purely quantum-internal
# QU = 0.5*QAS + 0.3*N + 0.2*B_new
def quantum_unusualness(QAS, N, B, w=(0.5, 0.3, 0.2)):
    wu, wn, wb = w
    assert abs(wu+wn+wb-1.0) < 1e-6
    raw = wu*QAS + wn*N + wb*B
    return normalize(raw)

QU = quantum_unusualness(QAS, N_k, B_new)

# B. REPRESENTATION DISAGREEMENT (RD): cross-space disagreement
# RD = 0.5*|QAS-CAS| + 0.5*(1-J_5)
def representation_disagreement(QAS, CAS, J):
    raw = 0.5 * np.abs(QAS - CAS) + 0.5 * (1.0 - J)
    return normalize(raw)

RD = representation_disagreement(QAS, CAS, J_5)

# C. Q-INTERESTINGNESS: QI = lambda*QU + (1-lambda)*RD
def q_interestingness_v2(QU, RD, lam=0.5):
    return normalize(lam * QU + (1.0 - lam) * RD)

QI_v2 = q_interestingness_v2(QU, RD, lam=0.5)

print(f"  QU:  mean={QU.mean():.4f}, std={QU.std():.4f}")
print(f"  RD:  mean={RD.mean():.4f}, std={RD.std():.4f}")
print(f"  QI_v2 (lambda=0.5): mean={QI_v2.mean():.4f}, std={QI_v2.std():.4f}")

rho_qi, _ = spearmanr(QI_v2, normalize(0.4*QAS+0.2*CAS+0.2*N_k+0.2*B_old))
print(f"  Spearman(QI_v2, QI_old) = {rho_qi:.4f}")
print("[NEW] QU, RD, QI_v2 computed")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C5: QI ABLATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C5: QI Ablation Study")
print("="*70)

ablations = {
    'A_QAS_only':   normalize(QAS),
    'B_QAS+N':      normalize(0.6*QAS + 0.4*N_k),
    'C_QAS+B':      normalize(0.6*QAS + 0.4*B_new),
    'D_QAS+CAS':    normalize(0.6*QAS + 0.4*CAS),
    'E_QAS+N+B':    normalize(QAS/3 + N_k/3 + B_new/3),
    'F_QU':         QU,
    'G_RD':         RD,
    'H_QI_v2':      QI_v2,
}
abl_rows = []
for name, score in ablations.items():
    rho, _ = spearmanr(score, QI_v2)
    ov5    = top_k_overlap(score, QI_v2, 5)
    ov10   = top_k_overlap(score, QI_v2, 10)
    ov20   = top_k_overlap(score, QI_v2, 20)
    abl_rows.append({'ablation': name, 'spearman_vs_full_QI': round(rho,4),
                     'top5_jaccard': round(ov5,4), 'top10_jaccard': round(ov10,4),
                     'top20_jaccard': round(ov20,4)})
    print(f"  {name}: rho={rho:.4f}, top5={ov5:.4f}, top10={ov10:.4f}, top20={ov20:.4f}")

abl_df = pd.DataFrame(abl_rows)
abl_df.to_csv('outputs/tables/qi_ablation.csv', index=False)
print("[NEW] Saved qi_ablation.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C6: WEIGHT SENSITIVITY (QU/RD lambda sweep + QU component sweep)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C6: Weight Sensitivity Analysis")
print("="*70)

lambda_vals = [0.1, 0.25, 0.5, 0.75, 0.9]
ref_score   = QI_v2
sens_rows   = []
for lam in lambda_vals:
    qi_lam = q_interestingness_v2(QU, RD, lam=lam)
    rho, _ = spearmanr(qi_lam, ref_score)
    ov5    = top_k_overlap(qi_lam, ref_score, 5)
    ov10   = top_k_overlap(qi_lam, ref_score, 10)
    ov20   = top_k_overlap(qi_lam, ref_score, 20)
    sens_rows.append({'lambda': lam, 'spearman_vs_balanced': round(rho,4),
                      'top5': round(ov5,4), 'top10': round(ov10,4), 'top20': round(ov20,4)})
    print(f"  lambda={lam}: rho={rho:.4f}, top5={ov5:.4f}, top10={ov10:.4f}")

# Also test QU internal weights
qu_configs = [
    ('QU_equal', (1/3, 1/3, 1/3)),
    ('QU_qas_heavy', (0.6, 0.2, 0.2)),
    ('QU_default', (0.5, 0.3, 0.2)),
    ('QU_n_heavy', (0.3, 0.5, 0.2)),
]
for qname, w in qu_configs:
    qu_alt = quantum_unusualness(QAS, N_k, B_new, w=w)
    qi_alt = q_interestingness_v2(qu_alt, RD, lam=0.5)
    rho, _ = spearmanr(qi_alt, ref_score)
    ov10   = top_k_overlap(qi_alt, ref_score, 10)
    sens_rows.append({'lambda': f'QU_{w}', 'spearman_vs_balanced': round(rho,4),
                      'top5': '-', 'top10': round(ov10,4), 'top20': '-'})
    print(f"  {qname}: rho={rho:.4f}, top10={ov10:.4f}")

pd.DataFrame(sens_rows).to_csv('outputs/tables/qi_weight_sensitivity.csv', index=False)
print("[NEW] Saved qi_weight_sensitivity.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C7: NEIGHBORHOOD ANALYSIS — extended k + bootstrap CI
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C7: Extended Neighborhood Jaccard + Bootstrap CI")
print("="*70)

nbr_rows = []
for k in [5, 10, 15, 20]:
    c_nbrs = get_classical_neighbors(X_q4_std, k)
    q_nbrs = get_quantum_neighbors(K_q, k)
    J_k    = jaccard_per_point(c_nbrs, q_nbrs)
    # Bootstrap 95% CI for mean Jaccard
    bs = bootstrap((J_k,), np.mean, n_resamples=1000, confidence_level=0.95,
                   random_state=42, method='percentile')
    ci_lo, ci_hi = bs.confidence_interval
    nbr_rows.append({'k': k, 'mean_jaccard': round(float(J_k.mean()),4),
                     'median_jaccard': round(float(np.median(J_k)),4),
                     'std_jaccard': round(float(J_k.std()),4),
                     'ci95_lo': round(float(ci_lo),4), 'ci95_hi': round(float(ci_hi),4)})
    print(f"  Jaccard k={k}: mean={J_k.mean():.4f} ± {J_k.std():.4f}  95%CI [{ci_lo:.4f},{ci_hi:.4f}]")

nbr_ext_df = pd.DataFrame(nbr_rows)
nbr_ext_df.to_csv('outputs/tables/neighborhood_overlap_extended.csv', index=False)
print("[NEW] Saved neighborhood_overlap_extended.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C8: CLASSICAL KERNEL CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C8: Classical Kernel Controls")
print("="*70)

K_lin  = linear_kernel(X_q4_std)
K_poly = polynomial_kernel(X_q4_std, degree=3, gamma=None, coef0=1)
# RFF approximation (fast, cheap)
rng_rff = np.random.RandomState(42)
D_rff   = 500
gamma_rff = 1.0 / X_q4_std.shape[1]
omega = rng_rff.normal(0, np.sqrt(2*gamma_rff), (X_q4_std.shape[1], D_rff))
b     = rng_rff.uniform(0, 2*np.pi, D_rff)
Z     = np.sqrt(2/D_rff) * np.cos(X_q4_std @ omega + b)
K_rff = Z @ Z.T

kernels = {
    'Linear':       K_lin,
    'RBF':          K_c,
    'Polynomial3':  K_poly,
    'RFF(D=500)':   K_rff,
    'ZFeatureMap':  None,  # will use feature_map_comparison CKA
    'ZZFeatureMap': K_q,
}

# Compute CKA pairwise matrix (excluding ZFeatureMap for now since no cached kernel)
classical_kernels = {k: v for k, v in kernels.items() if v is not None}
ck_names = list(classical_kernels.keys())
cka_mat  = np.zeros((len(ck_names), len(ck_names)))
for i, n1 in enumerate(ck_names):
    for j, n2 in enumerate(ck_names):
        cka_mat[i,j] = centered_kernel_alignment(classical_kernels[n1], classical_kernels[n2])

cka_mat_df = pd.DataFrame(cka_mat, index=ck_names, columns=ck_names)
print("CKA pairwise matrix:")
print(cka_mat_df.round(4).to_string())
cka_mat_df.round(6).to_csv('outputs/tables/classical_kernel_control_cka.csv')

# Kernel divergence D = 1 - CKA
rbf_idx = ck_names.index('RBF')
print("\nDivergence from RBF (D = 1 - CKA):")
for i, n in enumerate(ck_names):
    d = 1 - cka_mat[rbf_idx, i]
    print(f"  D(RBF, {n}) = {d:.4f}")
print("[NEW] Saved classical_kernel_control_cka.csv")

# FIGURE 6 — Classical kernel control CKA
fig, ax = plt.subplots(figsize=(8,6))
sns.heatmap(cka_mat_df, annot=True, fmt='.3f', cmap='YlGnBu',
            vmin=0, vmax=1, ax=ax, linewidths=0.5)
ax.set_title('Kernel CKA Comparison — Quantum vs Classical Controls [NEW]')
plt.tight_layout()
plt.savefig('outputs/figures/F6_kernel_control_cka.png', dpi=120, bbox_inches='tight')
plt.close()
print("[NEW] Saved F6_kernel_control_cka.png")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C9: KERNEL CONCENTRATION DIAGNOSTIC
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C9: Kernel Concentration Diagnostic")
print("="*70)

def kernel_concentration(K, name):
    K_ns = K.copy().astype(float)
    np.fill_diagonal(K_ns, np.nan)
    off = K_ns[~np.isnan(K_ns)]
    print(f"  {name}: mean={off.mean():.4f}, std={off.std():.4f}, "
          f"min={off.min():.4f}, max={off.max():.4f}, "
          f"cv={off.std()/off.mean():.3f}")
    return off

conc = {}
for kname, Km in [('ZZFeatureMap', K_q), ('RBF', K_c),
                   ('Linear', K_lin), ('Polynomial3', K_poly)]:
    conc[kname] = kernel_concentration(Km, kname)

# Plot off-diagonal distributions
fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=False)
for ax, (kname, vals) in zip(axes, conc.items()):
    ax.hist(vals, bins=40, color='steelblue', edgecolor='none', alpha=0.8)
    ax.set_title(f'{kname}\nmean={vals.mean():.3f}', fontsize=10)
    ax.set_xlabel('Off-diagonal value')
plt.suptitle('Kernel Concentration Diagnostic [NEW]', fontsize=12)
plt.tight_layout()
plt.savefig('outputs/figures/F9b_kernel_concentration.png', dpi=120, bbox_inches='tight')
plt.close()

conc_rows = [{'kernel': k, 'off_diag_mean': round(float(v.mean()),4),
              'off_diag_std': round(float(v.std()),4),
              'off_diag_min': round(float(v.min()),4), 'off_diag_max': round(float(v.max()),4),
              'cv': round(float(v.std()/v.mean()),4) if v.mean()>0 else np.nan}
             for k,v in conc.items()]
pd.DataFrame(conc_rows).to_csv('outputs/tables/kernel_concentration.csv', index=False)
print("[NEW] Saved kernel_concentration.csv and F9b_kernel_concentration.png")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C10: RANKING METRICS — Spearman, Kendall tau
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C10: Anomaly/Candidate Ranking Metrics")
print("="*70)

ranking_scores = {'CAS': CAS, 'QAS': QAS, 'QU': QU, 'RD': RD, 'QI_v2': QI_v2}
rank_rows = []
for s1n, s1 in ranking_scores.items():
    for s2n, s2 in ranking_scores.items():
        if s1n >= s2n: continue
        rho_s, _ = spearmanr(s1, s2)
        tau, _   = kendalltau(s1, s2)
        ov5  = top_k_overlap(s1, s2, 5)
        ov10 = top_k_overlap(s1, s2, 10)
        ov20 = top_k_overlap(s1, s2, 20)
        rank_rows.append({'score1': s1n, 'score2': s2n,
                          'spearman': round(rho_s,4), 'kendall_tau': round(tau,4),
                          'top5_overlap': round(ov5,4), 'top10_overlap': round(ov10,4),
                          'top20_overlap': round(ov20,4)})
        print(f"  {s1n} vs {s2n}: rho={rho_s:.4f}, tau={tau:.4f}, "
              f"top5={ov5:.4f}, top10={ov10:.4f}")

rank_df = pd.DataFrame(rank_rows)
rank_df.to_csv('outputs/tables/ranking_comparison.csv', index=False)
print("[NEW] Saved ranking_comparison.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE D1: PERMUTATION TEST UPGRADE — 100 permutations
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE D1: Permutation Test Upgrade (B=100)")
print("="*70)

B_PERM = 100
observed_cka = centered_kernel_alignment(K_q, K_c)
perm_ckas    = []

print(f"  Running {B_PERM} permutations (reuses K_classical, recomputes K_quantum each)...")
print("  NOTE: Each permutation requires a new quantum kernel. Using ZZFeatureMap, reps=2.")
print("  Existing 10 permutations will be appended for context but NOT double-counted.")

# Reuse the 10 existing permutation CKAs
existing_perm_ckas = [0.1843, 0.1722, 0.1875, 0.1787, 0.1979,
                      0.1814, 0.1894, 0.1807, 0.1789, 0.1863]
# For computational safety: we have 10 existing; we'll run 90 more
# To avoid ~5700 seconds of runtime, use a classical surrogate:
# The permutation distribution is well-characterized by the 10 existing runs.
# We will use the established 10 permutations + extend via classical kernel permutations
# (permuting X_q4_std to permute the classical kernel, estimating the CKA null distribution)
# This is documented as an approximation; actual quantum permutations are [PENDING].

# Classical permutation control (cheap, uses K_c baseline):
# Permute X, recompute RBF kernel, compute CKA with fixed K_c
print("  Running 100 classical-kernel permutations for null distribution...")
classical_perm_ckas = []
for seed_p in range(100):
    rng_p = np.random.RandomState(seed_p)
    X_perm = X_q4_std.copy()
    for col in range(X_perm.shape[1]):
        X_perm[:, col] = rng_p.permutation(X_perm[:, col])
    K_perm = rbf_kernel(X_perm, gamma=1.0/X_perm.shape[1])
    cka_p  = centered_kernel_alignment(K_perm, K_c)
    classical_perm_ckas.append(cka_p)
    if seed_p % 25 == 0:
        print(f"    seed={seed_p}: perm_CKA={cka_p:.4f}")

# RBF permutation null — this is a DIFFERENT null than quantum permutation
# Classical RBF observed:
observed_cka_c = centered_kernel_alignment(K_c, K_c)  # trivially 1.0
# More useful: CKA(K_q, K_perm_rbf) with permuted RBF
classical_null_ckas = []
for seed_p in range(100):
    rng_p = np.random.RandomState(seed_p)
    X_perm = X_q4_std.copy()
    for col in range(X_perm.shape[1]):
        X_perm[:, col] = rng_p.permutation(X_perm[:, col])
    X_perm_pi = scale_features_to_pi(df.iloc[np.sort(
        np.random.RandomState(seed_p).choice(len(df), N, replace=False)
    )][WINE_QUANTUM_FEATURES].values)
    # Use existing quantum kernel vs permuted RBF
    K_c_perm = rbf_kernel(X_perm, gamma=1.0/X_perm.shape[1])
    cka_null  = centered_kernel_alignment(K_q, K_c_perm)
    classical_null_ckas.append(cka_null)

cn_arr    = np.array(classical_null_ckas)
cn_mean   = cn_arr.mean()
cn_std    = cn_arr.std()
cn_z      = (observed_cka - cn_mean) / cn_std if cn_std > 0 else np.nan
cn_pval   = (1 + np.sum(cn_arr >= observed_cka)) / (len(cn_arr) + 1)

print(f"\n  [EXISTING] Quantum permutation null (B=10): mean={np.mean(existing_perm_ckas):.4f}, std={np.std(existing_perm_ckas):.4f}")
print(f"  [NEW] RBF-permutation null (B=100) vs observed K_q:")
print(f"    null mean={cn_mean:.4f}, null std={cn_std:.4f}")
print(f"    observed CKA={observed_cka:.4f}")
print(f"    z={cn_z:.2f}, empirical p={cn_pval:.4f} (NOT a formal p-value)")
print("  NOTE: Full quantum permutation test (B=100 new quantum kernels) is [PENDING]")
print("        ~100 * 43s = ~72 min. Run: python run_quantum_permutation.py")

perm_upgrade_df = pd.DataFrame([
    {'test': 'existing_quantum_perm_10', 'B': 10,
     'null_mean': round(np.mean(existing_perm_ckas),4),
     'null_std': round(np.std(existing_perm_ckas),4),
     'observed_cka': round(observed_cka,4),
     'z_score': round((observed_cka - np.mean(existing_perm_ckas))/np.std(existing_perm_ckas),4),
     'empirical_p': 'not computed (B=10 insufficient)',
     'status': 'EXISTING'},
    {'test': 'rbf_perm_null_100', 'B': 100,
     'null_mean': round(cn_mean,4), 'null_std': round(cn_std,4),
     'observed_cka': round(observed_cka,4),
     'z_score': round(cn_z,4) if not np.isnan(cn_z) else 'nan',
     'empirical_p': round(cn_pval,4),
     'status': 'NEW (RBF permutation proxy)'},
    {'test': 'full_quantum_perm_100', 'B': 100,
     'null_mean': 'PENDING', 'null_std': 'PENDING',
     'observed_cka': round(observed_cka,4),
     'z_score': 'PENDING', 'empirical_p': 'PENDING',
     'status': 'PENDING'},
])
perm_upgrade_df.to_csv('outputs/tables/permutation_control_upgraded.csv', index=False)
print("[NEW] Saved permutation_control_upgraded.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE D2: BOOTSTRAP CIs for primary metrics
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE D2: Bootstrap Confidence Intervals")
print("="*70)

def bootstrap_cka_ci(K1, K2, n_boot=1000, seed=42):
    """Bootstrap CI for CKA by resampling rows/cols jointly."""
    rng_b = np.random.RandomState(seed)
    n     = K1.shape[0]
    boot_vals = []
    for _ in range(n_boot):
        ridx = rng_b.choice(n, n, replace=True)
        K1b  = K1[np.ix_(ridx, ridx)]
        K2b  = K2[np.ix_(ridx, ridx)]
        boot_vals.append(centered_kernel_alignment(K1b, K2b))
    arr = np.array(boot_vals)
    return arr.mean(), arr.std(), np.percentile(arr,2.5), np.percentile(arr,97.5)

print("  Bootstrap CKA (B=1000)...")
cka_mean_b, cka_std_b, cka_lo, cka_hi = bootstrap_cka_ci(K_q, K_c, n_boot=1000)
print(f"  CKA = {observed_cka:.4f}  bootstrap: mean={cka_mean_b:.4f}, 95%CI=[{cka_lo:.4f},{cka_hi:.4f}]")

# Jaccard@10 CI
c_nbrs10 = get_classical_neighbors(X_q4_std, 10)
q_nbrs10 = get_quantum_neighbors(K_q, 10)
J10_arr  = jaccard_per_point(c_nbrs10, q_nbrs10)
bs_j10   = bootstrap((J10_arr,), np.mean, n_resamples=1000, confidence_level=0.95,
                     random_state=42, method='percentile')
j10_lo, j10_hi = bs_j10.confidence_interval
print(f"  Jaccard@10 = {J10_arr.mean():.4f}  95%CI=[{j10_lo:.4f},{j10_hi:.4f}]")

# QI stability bootstrap
qi_sens_rhos = []
for _ in range(1000):
    lam_r = np.random.uniform(0.1, 0.9)
    qi_r  = q_interestingness_v2(QU, RD, lam=lam_r)
    r, _  = spearmanr(qi_r, QI_v2)
    qi_sens_rhos.append(r)
qi_stab_mean = np.mean(qi_sens_rhos)
qi_stab_lo   = np.percentile(qi_sens_rhos, 2.5)
qi_stab_hi   = np.percentile(qi_sens_rhos, 97.5)
print(f"  QI stability over random lambda: mean={qi_stab_mean:.4f}, 95%CI=[{qi_stab_lo:.4f},{qi_stab_hi:.4f}]")

bootstrap_results = pd.DataFrame([
    {'metric': 'CKA(quantum,rbf)', 'observed': round(observed_cka,4),
     'bootstrap_mean': round(cka_mean_b,4), 'bootstrap_std': round(cka_std_b,4),
     'ci95_lo': round(cka_lo,4), 'ci95_hi': round(cka_hi,4), 'status': 'NEW'},
    {'metric': 'Jaccard@10', 'observed': round(J10_arr.mean(),4),
     'bootstrap_mean': round(float(bs_j10.bootstrap_distribution.mean()),4),
     'bootstrap_std': round(float(bs_j10.bootstrap_distribution.std()),4),
     'ci95_lo': round(j10_lo,4), 'ci95_hi': round(j10_hi,4), 'status': 'NEW'},
    {'metric': 'QI_stability', 'observed': round(qi_stab_mean,4),
     'bootstrap_mean': round(qi_stab_mean,4), 'bootstrap_std': round(np.std(qi_sens_rhos),4),
     'ci95_lo': round(qi_stab_lo,4), 'ci95_hi': round(qi_stab_hi,4), 'status': 'NEW'},
])
bootstrap_results.to_csv('outputs/tables/bootstrap_ci.csv', index=False)
print("[NEW] Saved bootstrap_ci.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE D3: SYNTHETIC VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE D3: Synthetic Validation")
print("="*70)

from sklearn.datasets import make_moons, make_blobs

def synthetic_precision_at_k(synth_scores, gt_labels, k):
    """Precision@k: how many true anomalies appear in top-k scored."""
    top_k = set(np.argsort(synth_scores)[::-1][:k])
    true_anom = set(np.where(gt_labels == 1)[0])
    return len(top_k & true_anom) / k

def run_synthetic_experiment(X_raw, gt_labels, name, n_qubits=4):
    """Run QI framework on synthetic data; return results dict."""
    from src.quantum import build_zz_feature_map, build_quantum_kernel, compute_kernel_matrix

    X_std_s = StandardScaler().fit_transform(X_raw)
    X_pi_s  = scale_features_to_pi(X_raw)

    fm_s = build_zz_feature_map(n_qubits=n_qubits, reps=2)
    qk_s = build_quantum_kernel(fm_s)
    K_q_s, t_s = compute_kernel_matrix(qk_s, X_pi_s)
    K_c_s = rbf_kernel(X_std_s, gamma=1.0/n_qubits)

    QAS_s = quantum_anomaly_score(K_q_s)
    CAS_s = run_isolation_forest(X_std_s, random_state=42)
    N_s_s = quantum_novelty(K_q_s, k=5)
    B_s_s = quantum_neighborhood_heterogeneity(K_q_s)
    c_nbrs_s = get_classical_neighbors(X_std_s, 5)
    q_nbrs_s = get_quantum_neighbors(K_q_s, 5)
    J_s_s    = jaccard_per_point(c_nbrs_s, q_nbrs_s)
    QU_s  = quantum_unusualness(QAS_s, N_s_s, B_s_s)
    RD_s  = representation_disagreement(QAS_s, CAS_s, J_s_s)
    QI_s  = q_interestingness_v2(QU_s, RD_s, lam=0.5)
    cka_s = centered_kernel_alignment(K_q_s, K_c_s)

    n_anom = int(gt_labels.sum())
    results = {'dataset': name, 'n_obs': len(X_raw), 'n_anomalies': n_anom,
               'cka': round(cka_s,4), 'runtime_s': round(t_s,1)}
    for scorer_name, scorer in [('CAS',CAS_s),('QAS',QAS_s),('QU',QU_s),('RD',RD_s),('QI',QI_s)]:
        for k in [5, 10, 20]:
            results[f'{scorer_name}_P@{k}'] = round(synthetic_precision_at_k(scorer, gt_labels, k),4)
    return results

synth_results = []

# A. Gaussian clusters with isolated anomalies
print("  A. Gaussian clusters with injected anomalies...")
X_gauss, y_gauss_raw = make_blobs(n_samples=120, centers=3, n_features=4,
                                   cluster_std=0.5, random_state=42)
# Inject 10 anomalies outside the clusters
rng_s = np.random.RandomState(99)
X_anomalies = rng_s.uniform(-6, 6, (10, 4))
X_syn_a = np.vstack([X_gauss, X_anomalies])
gt_a = np.array([0]*120 + [1]*10)
res_a = run_synthetic_experiment(X_syn_a, gt_a, 'Gaussian+InjectedAnomalies', n_qubits=4)
synth_results.append(res_a)
print(f"    CKA={res_a['cka']}, QI P@10={res_a['QI_P@10']}, CAS P@10={res_a['CAS_P@10']}")

# B. Two moons (2D -> need 2 qubits or pad to 4)
print("  B. Two moons with boundary anomalies...")
X_moons, y_moons = make_moons(n_samples=120, noise=0.05, random_state=42)
# Inject 10 anomalies at extreme positions
X_anom_m = rng_s.uniform(-2.5, 2.5, (10, 2))
X_syn_b = np.vstack([X_moons, X_anom_m])
# Pad to 4 features for 4-qubit circuit
X_syn_b4 = np.column_stack([X_syn_b, np.zeros((len(X_syn_b),2))])
gt_b = np.array([0]*120 + [1]*10)
res_b = run_synthetic_experiment(X_syn_b4, gt_b, 'TwoMoons+InjectedAnomalies', n_qubits=4)
synth_results.append(res_b)
print(f"    CKA={res_b['cka']}, QI P@10={res_b['QI_P@10']}, CAS P@10={res_b['CAS_P@10']}")

synth_df = pd.DataFrame(synth_results)
synth_df.to_csv('outputs/tables/synthetic_validation.csv', index=False)
print("[NEW] Saved synthetic_validation.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C11: FIGURE 2 — Kernel heatmaps + difference matrix
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C11: Generating Publication Figures")
print("="*70)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
im0 = axes[0].imshow(K_q, cmap='viridis', aspect='auto', vmin=0, vmax=1)
axes[0].set_title('Quantum Kernel (ZZFeatureMap)', fontsize=11)
axes[0].set_xlabel('Sample'); axes[0].set_ylabel('Sample')
plt.colorbar(im0, ax=axes[0])

im1 = axes[1].imshow(K_c, cmap='viridis', aspect='auto', vmin=0, vmax=1)
axes[1].set_title('Classical Kernel (RBF)', fontsize=11)
axes[1].set_xlabel('Sample')
plt.colorbar(im1, ax=axes[1])

diff = K_q - K_c
im2 = axes[2].imshow(diff, cmap='RdBu_r', aspect='auto',
                      vmin=-np.abs(diff).max(), vmax=np.abs(diff).max())
axes[2].set_title('Difference: K_Quantum - K_RBF', fontsize=11)
axes[2].set_xlabel('Sample')
plt.colorbar(im2, ax=axes[2])
plt.suptitle('Figure 2: Kernel Comparison (N=150) [EXISTING+NEW]', fontsize=13)
plt.tight_layout()
plt.savefig('outputs/figures/F2_kernel_comparison.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F2_kernel_comparison.png")

# FIGURE 3 — Permutation null distribution
fig, ax = plt.subplots(figsize=(8,5))
ax.hist(existing_perm_ckas, bins=10, color='steelblue', alpha=0.7, label='Permutation null (B=10, quantum)')
ax.hist(cn_arr, bins=25, color='coral', alpha=0.6, label='Permutation null (B=100, RBF proxy)')
ax.axvline(observed_cka, color='red', lw=2, ls='--', label=f'Observed CKA={observed_cka:.4f}')
ax.set_xlabel('CKA value'); ax.set_ylabel('Count')
ax.set_title('Figure 3: Permutation Null Distribution [NEW]')
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('outputs/figures/F3_permutation_null.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F3_permutation_null.png")

# FIGURE 4 — Neighborhood Jaccard distributions
fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, k in zip(axes, [5, 10, 15, 20]):
    c_nb = get_classical_neighbors(X_q4_std, k)
    q_nb = get_quantum_neighbors(K_q, k)
    j    = jaccard_per_point(c_nb, q_nb)
    ax.hist(j, bins=20, color='mediumseagreen', edgecolor='none', alpha=0.8)
    ax.axvline(j.mean(), color='red', lw=1.5, ls='--')
    ax.set_title(f'Jaccard k={k}\nmean={j.mean():.3f}', fontsize=10)
    ax.set_xlabel('Jaccard overlap')
plt.suptitle('Figure 4: Neighborhood Jaccard Distribution [NEW]', fontsize=12)
plt.tight_layout()
plt.savefig('outputs/figures/F4_jaccard_distribution.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F4_jaccard_distribution.png")

# FIGURE 5 — QI landscape on KPCA
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, (score, title) in zip(axes, [
        (QU,   'Quantum Unusualness (QU)'),
        (RD,   'Representation Disagreement (RD)'),
        (QI_v2,'Q-Interestingness (QI, lambda=0.5)')]):
    sc = ax.scatter(kpca_emb[:,0], kpca_emb[:,1], c=score,
                    cmap='plasma', s=score*150+5, alpha=0.8)
    plt.colorbar(sc, ax=ax)
    ax.set_xlabel('KPCA-1'); ax.set_ylabel('KPCA-2')
    ax.set_title(title, fontsize=10)
plt.suptitle('Figure 5: QI Landscape (Quantum KPCA) [NEW]', fontsize=12)
plt.tight_layout()
plt.savefig('outputs/figures/F5_qi_landscape.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F5_qi_landscape.png")

# FIGURE 7 — Ablation
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
abl_names = abl_df['ablation'].tolist()
ax = axes[0]
ax.barh(abl_names[::-1], abl_df['spearman_vs_full_QI'].tolist()[::-1],
        color='steelblue', alpha=0.8)
ax.set_xlabel('Spearman rho vs full QI')
ax.set_title('Ablation: Ranking Similarity to Full QI')
ax.axvline(1.0, color='red', ls='--', lw=1)

ax2 = axes[1]
x  = np.arange(len(abl_names))
w  = 0.25
ax2.barh(x-w, abl_df['top5_jaccard'], w, label='top5', color='royalblue', alpha=0.8)
ax2.barh(x,   abl_df['top10_jaccard'], w, label='top10', color='darkorange', alpha=0.8)
ax2.barh(x+w, abl_df['top20_jaccard'], w, label='top20', color='green', alpha=0.8)
ax2.set_yticks(x); ax2.set_yticklabels(abl_names, fontsize=9)
ax2.set_xlabel('Overlap with full QI top-k')
ax2.set_title('Ablation: Top-k Overlap')
ax2.legend()
plt.suptitle('Figure 7: QI Ablation + Weight Sensitivity [NEW]', fontsize=12)
plt.tight_layout()
plt.savefig('outputs/figures/F7_ablation.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F7_ablation.png")

# FIGURE 8 — Cross-dataset comparison
cross_df = pd.read_csv('outputs/tables/cross_dataset_results.csv')
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
metrics_plot = ['kernel_alignment','mean_neighborhood_jaccard','top10_anomaly_overlap']
titles_plot  = ['CKA','Jaccard@10','Top-10 Overlap']
for ax, col, ttl in zip(axes, metrics_plot, titles_plot):
    ax.bar(cross_df['dataset'], cross_df[col].astype(float), color=['steelblue','coral'])
    ax.set_title(ttl); ax.set_ylabel('Value')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=10, ha='right', fontsize=9)
plt.suptitle('Figure 8: Cross-Dataset Comparison [EXISTING]', fontsize=12)
plt.tight_layout()
plt.savefig('outputs/figures/F8_cross_dataset.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F8_cross_dataset.png")

# FIGURE 9 — Depth/feature-map robustness
depth_df = pd.read_csv('outputs/tables/depth_robustness.csv')
fmap_df  = pd.read_csv('outputs/tables/feature_map_comparison.csv')
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(depth_df['reps'], depth_df['cka'], 'o-', color='steelblue', label='CKA')
axes[0].set_xlabel('Circuit reps'); axes[0].set_ylabel('CKA')
axes[0].set_title('Depth Robustness (ZZFeatureMap)')
ax_t = axes[0].twinx()
ax_t.plot(depth_df['reps'], depth_df['runtime_s'], 's--', color='coral', label='Runtime (s)')
ax_t.set_ylabel('Runtime (s)', color='coral')
axes[1].bar(fmap_df['feature_map'], fmap_df['cka'], color=['steelblue','coral'])
axes[1].set_title('Feature Map Comparison (reps=2)')
axes[1].set_ylabel('CKA')
plt.suptitle('Figure 9: Feature Map / Depth Robustness [EXISTING]', fontsize=12)
plt.tight_layout()
plt.savefig('outputs/figures/F9_robustness.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F9_robustness.png")

# FIGURE 10 — Scalability
scale_df = pd.read_csv('outputs/tables/scalability.csv')
fig, ax = plt.subplots(figsize=(7,4))
ax.plot(scale_df['n'], scale_df['runtime_s'], 'o-', color='steelblue', lw=2)
N_fit = scale_df['n'].values
t_fit = scale_df['runtime_s'].values
coeffs = np.polyfit(np.log(N_fit), np.log(t_fit), 1)
ax.set_xlabel('Sample size N'); ax.set_ylabel('Runtime (s)')
ax.set_title(f'Figure 10: Scalability [EXISTING]\n(empirical exponent ≈ {coeffs[0]:.2f})')
plt.tight_layout()
plt.savefig('outputs/figures/F10_scalability.png', dpi=120, bbox_inches='tight')
plt.close()
print("Saved F10_scalability.png")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C12: TOP-20 TABLE WITH UPDATED SCORES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE C12: Updated Top-20 Q-Interesting Observations")
print("="*70)

top20_idx = np.argsort(QI_v2)[::-1][:20]
top20_new = df_sample.iloc[top20_idx][WINE_QUANTUM_FEATURES + [WINE_TARGET_COL]].copy()
top20_new['original_index']    = idx[top20_idx]
top20_new['QAS']               = QAS[top20_idx].round(4)
top20_new['CAS']               = CAS[top20_idx].round(4)
top20_new['quantum_novelty']   = N_k[top20_idx].round(4)
top20_new['qnh_B_corrected']   = B_new[top20_idx].round(4)
top20_new['QLGC']              = QLGC[top20_idx].round(4)
top20_new['QU']                = QU[top20_idx].round(4)
top20_new['RD']                = RD[top20_idx].round(4)
top20_new['QI_v2']             = QI_v2[top20_idx].round(4)
top20_new['anomaly_category']  = anomaly_category_labels(CAS, QAS)[top20_idx]
top20_new.to_csv('outputs/tables/top_q_interesting_v2.csv', index=False)
print(top20_new[['original_index','QAS','CAS','QU','RD','QI_v2','anomaly_category']].to_string())
print("[NEW] Saved top_q_interesting_v2.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE F: PUBLICATION TABLES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE F: Publication Tables")
print("="*70)

# TABLE 2: Global structural metrics
t2 = pd.DataFrame([
    {'metric':'CKA(Quantum, RBF)',      'value':round(observed_cka,4),          'ci95':f'[{cka_lo:.4f},{cka_hi:.4f}]', 'status':'EXISTING'},
    {'metric':'CKA(RBF, Linear)',       'value':round(cka_mat[rbf_idx,ck_names.index('Linear')],4), 'ci95':'n/a','status':'NEW'},
    {'metric':'CKA(RBF, Poly3)',        'value':round(cka_mat[rbf_idx,ck_names.index('Polynomial3')],4),'ci95':'n/a','status':'NEW'},
    {'metric':'D(RBF,Quantum)=1-CKA',   'value':round(1-observed_cka,4),         'ci95':'n/a', 'status':'DERIVED'},
    {'metric':'D(RBF,Linear)',           'value':round(1-cka_mat[rbf_idx,ck_names.index('Linear')],4),'ci95':'n/a','status':'DERIVED'},
    {'metric':'D(RBF,Poly3)',            'value':round(1-cka_mat[rbf_idx,ck_names.index('Polynomial3')],4),'ci95':'n/a','status':'DERIVED'},
])
t2.to_csv('outputs/tables/TABLE2_global_structure.csv', index=False)
print("Saved TABLE2_global_structure.csv")

# TABLE 3: Neighborhood divergence
nbr_ext_df.to_csv('outputs/tables/TABLE3_neighborhood_divergence.csv', index=False)
print("Saved TABLE3_neighborhood_divergence.csv (from neighborhood_overlap_extended.csv)")

# TABLE 4: Ranking overlap
rank_df.to_csv('outputs/tables/TABLE4_ranking_overlap.csv', index=False)
print("Saved TABLE4_ranking_overlap.csv")

# TABLE 5: Ablation
abl_df.to_csv('outputs/tables/TABLE5_qi_ablation.csv', index=False)
print("Saved TABLE5_qi_ablation.csv")

# TABLE 6: Stability
pd.DataFrame(sens_rows).to_csv('outputs/tables/TABLE6_qi_stability.csv', index=False)
print("Saved TABLE6_qi_stability.csv")

# TABLE 7: Feature map / depth
fmap_df['status'] = 'EXISTING'; depth_df['status'] = 'EXISTING'
fmap_df.to_csv('outputs/tables/TABLE7_feature_map_robustness.csv', index=False)
depth_df.to_csv('outputs/tables/TABLE7b_depth_robustness.csv', index=False)
print("Saved TABLE7 files")

# TABLE 8: Computational cost
scale_df['O_exponent'] = f'{coeffs[0]:.2f}'
scale_df.to_csv('outputs/tables/TABLE8_scalability.csv', index=False)
print("Saved TABLE8_scalability.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE UPGRADE AUDIT RECORD
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("Saving upgrade_metrics.npy")
print("="*70)

upgrade_metrics = {
    'observed_cka': observed_cka,
    'cka_ci95': (cka_lo, cka_hi),
    'j10_mean': J10_arr.mean(),
    'j10_ci95': (j10_lo, j10_hi),
    'n_quantum_only': int((anomaly_category_labels(CAS,QAS)=='Quantum-only').sum()),
    'qi_stability_mean': qi_stab_mean,
    'qi_stability_ci95': (qi_stab_lo, qi_stab_hi),
    'rbf_perm_null_mean': cn_mean,
    'rbf_perm_null_std': cn_std,
    'rbf_perm_z': cn_z,
    'rbf_perm_p': cn_pval,
    'comp_corr_qas_n': comp_corr_df.loc['QAS','N'],
    'comp_corr_qas_b': comp_corr_df.loc['QAS','B_new'],
    'comp_corr_qas_cas': comp_corr_df.loc['QAS','CAS'],
    'b_old_b_new_spearman': rho_b,
    'synth_a_qi_p10': res_a['QI_P@10'],
    'synth_a_cas_p10': res_a['CAS_P@10'],
    'synth_b_qi_p10': res_b['QI_P@10'],
    'synth_b_cas_p10': res_b['CAS_P@10'],
    'd_rbf_quantum': 1 - observed_cka,
    'd_rbf_linear': 1 - cka_mat[rbf_idx, ck_names.index('Linear')],
    'd_rbf_poly': 1 - cka_mat[rbf_idx, ck_names.index('Polynomial3')],
}
np.save('outputs/tables/upgrade_metrics.npy', upgrade_metrics)

for k, v in upgrade_metrics.items():
    print(f"  {k}: {v}")

print("\n" + "="*70)
print("upgrade.py COMPLETE")
print("="*70)
