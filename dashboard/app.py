"""
dashboard/app.py — Streamlit dashboard for Q-Interestingness research project.
Launch: streamlit run dashboard/app.py (from the project root)
"""
import sys, os
sys.path.insert(0, os.path.abspath('..'))

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

st.set_page_config(page_title="Q-Interestingness Dashboard", layout="wide", page_icon="⚛️")

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = os.path.abspath('..')
KERNELS  = os.path.join(ROOT, 'outputs', 'kernels')
TABLES   = os.path.join(ROOT, 'outputs', 'tables')
FIGURES  = os.path.join(ROOT, 'outputs', 'figures')

def load_npy(fname): return np.load(os.path.join(KERNELS, fname))
def load_csv(fname): return pd.read_csv(os.path.join(TABLES, fname))
def fig_path(fname): return os.path.join(FIGURES, fname)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("⚛️ Q-Interestingness Dashboard")
st.markdown("""
**Q-Interestingness: Quantum Exploratory Data Analysis for Discovering Hidden Structure and Anomalies**

> *Does moving data into a quantum feature space change what exploratory analysis considers structurally unusual?*

---
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("Settings")
pct_threshold = st.sidebar.slider("Anomaly percentile threshold", 70, 99, 90, step=5)
top_k_show    = st.sidebar.slider("Top-N observations to show", 5, 20, 10, step=5)
cat_filter    = st.sidebar.multiselect(
    "Filter by anomaly category",
    ["Both", "Classical-only", "Quantum-only", "Neither"],
    default=["Both", "Classical-only", "Quantum-only", "Neither"]
)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    K_q   = load_npy('K_quantum.npy')
    K_c   = load_npy('K_classical.npy')
    top20 = load_csv('top_q_interesting_observations.csv')
    kpca  = np.load(os.path.join(TABLES, 'kpca_emb.npy'))
    return K_q, K_c, top20, kpca

K_q, K_c, top20_df, kpca_emb = get_data()

# Re-compute QAS/CAS for the slider threshold
QAS = (1 - (np.sum(K_q, axis=1) - np.diag(K_q)) / (K_q.shape[0] - 1))
QAS = (QAS - QAS.min()) / (QAS.max() - QAS.min() + 1e-10)
CAS = top20_df['CAS'].values  # proxy — only 20 obs

# ── Row 1 — Dataset Info ───────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Dataset", "UCI Red Wine Quality")
col2.metric("Quantum kernel N", K_q.shape[0])
col3.metric("Quantum features / qubits", 4)
col4.metric("Feature map", "ZZFeatureMap reps=2")

st.divider()

# ── Row 2 — Kernel Heatmaps ────────────────────────────────────────────────────
st.subheader("🔷 Kernel Heatmaps")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Quantum Kernel (ZZFeatureMap)**")
    fig, ax = plt.subplots(figsize=(5,4))
    im = ax.imshow(K_q, cmap='viridis', aspect='auto')
    ax.set_title(f"Quantum Kernel (N={K_q.shape[0]})")
    ax.set_xlabel("Sample index"); ax.set_ylabel("Sample index")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    st.pyplot(fig); plt.close()
with c2:
    st.markdown("**Classical RBF Kernel**")
    fig, ax = plt.subplots(figsize=(5,4))
    im = ax.imshow(K_c, cmap='viridis', aspect='auto')
    ax.set_title(f"Classical Kernel (N={K_c.shape[0]})")
    ax.set_xlabel("Sample index"); ax.set_ylabel("Sample index")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    st.pyplot(fig); plt.close()

st.divider()

# ── Row 3 — Q-Interestingness Map ─────────────────────────────────────────────
st.subheader("🗺️ Q-Interestingness Map (Quantum KPCA space)")
if os.path.exists(fig_path('09_q_interestingness_map.png')):
    st.image(fig_path('09_q_interestingness_map.png'), use_container_width=True)
else:
    st.info("Figure not yet generated — run notebooks first.")

st.divider()

# ── Row 4 — Anomaly Scatter ────────────────────────────────────────────────────
st.subheader("🔴 Classical vs Quantum Anomaly Scores")
if os.path.exists(fig_path('08_anomaly_scatter.png')):
    st.image(fig_path('08_anomaly_scatter.png'), use_container_width=True)

st.divider()

# ── Row 5 — Top observations table ────────────────────────────────────────────
st.subheader(f"🏆 Top-{top_k_show} Q-Interesting Observations")

filtered = top20_df[top20_df['anomaly_category'].isin(cat_filter)].head(top_k_show)
st.dataframe(
    filtered.style
        .background_gradient(subset=['QI_balanced'], cmap='plasma')
        .format({'QAS':'{:.4f}','CAS':'{:.4f}','quantum_novelty':'{:.4f}',
                 'quantum_boundary':'{:.4f}','QI_balanced':'{:.4f}'}),
    use_container_width=True
)

# Category counts
cat_counts = top20_df['anomaly_category'].value_counts()
st.markdown("**Category breakdown (top-20):**  " +
            "  |  ".join(f"**{c}**: {n}" for c, n in cat_counts.items()))

st.divider()

# ── Row 6 — Key Metrics ────────────────────────────────────────────────────────
st.subheader("📊 Key Research Metrics")

@st.cache_data
def load_metrics():
    try:
        final = load_csv('FINAL_RESEARCH_RESULTS.csv')
        return final
    except Exception:
        return None

final_df = load_metrics()
if final_df is not None:
    m = final_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kernel Alignment (CKA)", f"{m['kernel_alignment']:.4f}")
    c2.metric("Neighborhood Jaccard k=10", f"{m['mean_neighborhood_jaccard']:.4f}")
    c3.metric("Top-10 Anomaly Overlap", f"{m['top10_anomaly_overlap']:.4f}")
    c4.metric("Quantum-only Candidates", int(m['number_quantum_only_candidates']))
    c1b, c2b, c3b, _ = st.columns(4)
    c1b.metric("QI Rank Stability", f"{m['qi_rank_stability_spearman']:.4f}")
    c2b.metric("Permutation z-score", f"{m['permutation_z_score']:.2f}")
    c3b.metric("Feature map", m['feature_map'])

st.divider()

# ── Row 7 — Robustness ────────────────────────────────────────────────────────
st.subheader("🔬 Robustness Results")
rc1, rc2 = st.columns(2)
with rc1:
    st.markdown("**Circuit Depth Robustness**")
    try: st.dataframe(load_csv('depth_robustness.csv'), use_container_width=True)
    except: st.info("depth_robustness.csv not found")
with rc2:
    st.markdown("**Feature Map Comparison**")
    try: st.dataframe(load_csv('feature_map_comparison.csv'), use_container_width=True)
    except: st.info("feature_map_comparison.csv not found")

st.divider()

# ── Row 8 — Scalability ────────────────────────────────────────────────────────
st.subheader("⏱️ Scalability")
if os.path.exists(fig_path('11_scalability.png')):
    st.image(fig_path('11_scalability.png'), width=500)

try:
    sc_df = load_csv('scalability.csv')
    st.dataframe(sc_df, use_container_width=True)
except: pass

st.divider()

# ── Row 9 — Observation Detail ────────────────────────────────────────────────
st.subheader("🔍 Observation Detail")
obs_idx = st.selectbox("Select observation (from top-20)", top20_df['original_index'].tolist())
row = top20_df[top20_df['original_index'] == obs_idx].iloc[0]
detail_cols = st.columns(3)
detail_cols[0].json({
    'alcohol': float(row['alcohol']), 'volatile acidity': float(row['volatile acidity']),
    'sulphates': float(row['sulphates']), 'citric acid': float(row['citric acid']),
    'quality': int(row['quality']),
})
detail_cols[1].metric("Q-Interestingness", f"{row['QI_balanced']:.4f}")
detail_cols[1].metric("Quantum Anomaly Score", f"{row['QAS']:.4f}")
detail_cols[1].metric("Classical Anomaly Score", f"{row['CAS']:.4f}")
detail_cols[2].metric("Quantum Novelty", f"{row['quantum_novelty']:.4f}")
detail_cols[2].metric("Quantum Boundary", f"{row['quantum_boundary']:.4f}")
detail_cols[2].metric("Category", row['anomaly_category'])

st.caption("**Note**: This dashboard is for research demonstration only. "
           "Quantum computations are simulated classically (StatevectorSampler). "
           "No quantum hardware was used.")
