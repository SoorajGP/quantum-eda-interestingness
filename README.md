# Q-Interestingness: Quantum Exploratory Data Analysis

> **Research Question**: Does moving data into a quantum feature space change what exploratory analysis considers structurally unusual, and can this difference be quantified through a Q-Interestingness framework?

---

## Research Summary

| Metric | Value | Status |
|--------|-------|--------|
| Classical–Quantum Kernel Alignment (CKA) | **0.2484** | [EXISTING] |
| Neighborhood Jaccard Overlap (k=10) | **0.1004** | [EXISTING] |
| Top-10 Anomaly Overlap | **0.20** | [EXISTING] |
| Quantum-specific Exploratory Candidates | **13 / 150** | [EXISTING] |
| Classical Control Divergence vs RBF ($D = 1 - \text{CKA}$) | Quantum: **0.7516** vs Poly3: **0.3298** | [NEW] |
| QI_v2 Rank Stability (Spearman) | **0.9697** | [NEW] |

**Core Finding**: The quantum feature space via `ZZFeatureMap` produces a substantially different similarity structure from classical RBF kernels ($D = 0.7516$), diverging significantly more than classical non-linear controls.

---

## Architecture

```
q-interestingness/
  src/
    data.py              — data loading, scaling, sampling
    classical.py         — PCA, UMAP, IsolationForest, LOF, RBF kernel
    quantum.py           — ZZFeatureMap, FidelityQuantumKernel (Qiskit 2.5.2)
    metrics.py           — CKA, Jaccard neighborhoods, anomaly overlap
    interestingness.py   — QAS, novelty, QNH, QU, RD, QI_v2 composite
  notebooks/
    01_classical_eda.ipynb
    02_quantum_representation.ipynb
    03_quantum_similarity.ipynb
    04_comparative_analysis.ipynb
    05_q_interestingness.ipynb
    06_validation.ipynb
  outputs/
    figures/             — publication and exploratory plots
    tables/              — all CSV result tables
    kernels/             — K_quantum.npy, K_classical.npy, K_quantum2.npy
    RESEARCH_REPORT.md
    FINAL_RESEARCH_AUDIT.md
    CONFERENCE_READINESS.md
  dashboard/
    app.py               — Streamlit interactive dashboard
  requirements.txt
```

---

## Core Mathematical Framework

### Quantum State Mapping
$$x \to |\psi(x)\rangle = U_{\Phi(x)}|0\rangle^{\otimes n}$$

Using `ZZFeatureMap` with 2 repetitions and linear entanglement:
$$U_{\Phi(x)} = \exp\left(i \sum_j x_j Z_j + \sum_{j < k} (\pi - x_j)(\pi - x_k) Z_j Z_k\right)$$

### Quantum Kernel Similarity
$$S(x_i, x_j) = |\langle\psi(x_i)|\psi(x_j)\rangle|^2$$

### Q-Interestingness Framework (QI_v2)

The framework decomposes exploratory score assignment into internal quantum geometry and cross-representation disagreement:

#### 1. Quantum Unusualness (QU)
Measures structural isolation and novelty strictly within the quantum feature space:
$$\text{QU}(x) = 0.5 \cdot \text{QAS}(x) + 0.3 \cdot N(x) + 0.2 \cdot B(x)$$

* **QAS**: Global Quantum Anomaly Score = $1 - \frac{1}{N-1}\sum_{j \neq i} K_{ij}$
* **N(x)**: Local Quantum Novelty = $1 - \text{mean}(K_{i, \text{top-}k})$
* **B(x)**: Quantum Neighborhood Heterogeneity (QNH) = $\text{nanvar}_{j \neq i}(K_{ij})$ (excluding self-similarity $K_{ii}=1$)

#### 2. Representation Disagreement (RD)
Measures divergence between classical and quantum representations:
$$\text{RD}(x) = 0.5 \cdot |\text{QAS}(x) - \text{CAS}(x)| + 0.5 \cdot (1 - J_5(x))$$

* **CAS**: Classical Anomaly Score (Isolation Forest)
* **$J_5(x)$**: Neighborhood Jaccard overlap ($k=5$) between classical Euclidean and quantum kernel nearest neighbors

#### 3. Composite Metric (QI_v2)
$$\text{QI\_v2}(x) = 0.5 \cdot \text{QU}(x) + 0.5 \cdot \text{RD}(x)$$

---

## Limitations

1. Quantum computations use classical statevector simulation — **no quantum hardware** was used.
2. Quantum kernel limited to deterministic subsamples ($N=150$) due to $O(N^2)$ simulation cost.
3. No claim of quantum computational advantage or superiority over classical anomaly detection is made.
4. Synthetic validation confirms sensitivity to structure but demonstrates classical methods remain superior for trivial spatial outliers.

---

## Important Scientific Positioning

> Quantum-specific high-scoring observations are designated as **"Quantum-specific exploratory candidates"** rather than proven anomalies. The framework is designed for exploratory data discovery and complementary hypothesis generation.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run research upgrade pipeline and audit
python upgrade.py
python generate_audit.py
python generate_final_outputs.py

# Launch interactive dashboard
streamlit run dashboard/app.py
```
