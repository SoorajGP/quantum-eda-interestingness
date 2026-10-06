# Q-Interestingness: Quantum Exploratory Data Analysis

> **Research Question**: Does moving data into a quantum feature space change what exploratory analysis considers structurally unusual, and can this difference be quantified through a Q-Interestingness framework?

---

## Research Summary

| Metric | Value |
|--------|-------|
| Classical–Quantum Kernel Alignment (CKA) | **0.2484** |
| Neighborhood Jaccard Overlap (k=10) | **0.1004** |
| Top-10 Anomaly Overlap | **0.20** |
| Quantum-specific Exploratory Candidates | **13 / 150** |
| Q-Interestingness Rank Stability (Spearman) | **0.7977** |
| Permutation Control z-score | **9.14** |

**Conclusion**: Category A — Strong evidence of complementary quantum exploratory structure.

---

## Architecture

```
q-interestingness/
  src/
    data.py              — data loading, scaling, sampling
    classical.py         — PCA, UMAP, IsolationForest, LOF, RBF kernel
    quantum.py           — ZZFeatureMap, FidelityQuantumKernel (Qiskit 2.5.2)
    metrics.py           — CKA, Jaccard neighborhoods, anomaly overlap
    interestingness.py   — QAS, novelty, boundary, Q-Interestingness composite
  notebooks/
    01_classical_eda.ipynb
    02_quantum_representation.ipynb
    03_quantum_similarity.ipynb
    04_comparative_analysis.ipynb
    05_q_interestingness.ipynb
    06_validation.ipynb
  outputs/
    figures/             — all PNG plots (11 figures)
    tables/              — all CSV result tables
    kernels/             — K_quantum.npy, K_classical.npy
    RESEARCH_REPORT.md
  dashboard/
    app.py               — Streamlit interactive dashboard
  requirements.txt
```

---

## Installation

```powershell
# Install dependencies (Python 3.10–3.13 required)
pip install -r requirements.txt
```

**Verified environment:**
- Python 3.13.14
- Qiskit 2.5.2
- qiskit-machine-learning 0.9.1
- scikit-learn 1.9.1
- numpy 2.5.3

---

## Execution Order

Run notebooks in order:

```powershell
# From the project root directory:
python run_notebooks.py
```

Or individually:

```powershell
python -m nbconvert --to notebook --execute notebooks/01_classical_eda.ipynb --output notebooks/01_classical_eda.ipynb
python -m nbconvert --to notebook --execute notebooks/02_quantum_representation.ipynb ...
# etc.
```

---

## Datasets

| Dataset | Source | Observations | Features | Quantum Features |
|---------|--------|-------------|---------|-----------------|
| UCI Red Wine Quality | [UCI ML Repository](https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv) | 1,599 | 11 | alcohol, volatile acidity, sulphates, citric acid |
| sklearn Wine | `sklearn.datasets.load_wine()` | 178 | 13 | top-4 by variance |

---

## Methodology

### Quantum Feature Encoding

Data is mapped to quantum states via ZZFeatureMap:

$$x \rightarrow |\psi(x)\rangle$$

Quantum similarity (fidelity):

$$S(x_i, x_j) = |\langle\psi(x_i)|\psi(x_j)\rangle|^2$$

### Q-Interestingness Composite Score

$$QI(x) = w_q \cdot QAS(x) + w_c \cdot CAS(x) + w_n \cdot N(x) + w_b \cdot B(x)$$

Default weights: wq=0.40, wc=0.20, wn=0.20, wb=0.20

| Component | Description |
|-----------|-------------|
| QAS | Quantum Anomaly Score = 1 − mean quantum similarity |
| CAS | Classical Anomaly Score (IsolationForest) |
| N(x) | Quantum Novelty = 1 − mean similarity to top-k neighbors |
| B(x) | Quantum Boundary = variance of kernel row (prototype metric) |

### Centered Kernel Alignment (CKA)

$$A(K_1, K_2) = \frac{\langle K_{1c}, K_{2c} \rangle_F}{\|K_{1c}\|_F \|K_{2c}\|_F}$$

where $H = I - \mathbf{1}\mathbf{1}^T/n$, $K_c = HKH$

---

## Key Output Files

| File | Description |
|------|-------------|
| `outputs/tables/FINAL_RESEARCH_RESULTS.csv` | Primary research metrics |
| `outputs/tables/FINAL_EXPERIMENT_LOG.csv` | All experiment configurations |
| `outputs/tables/top_q_interesting_observations.csv` | Top-20 Q-interesting observations |
| `outputs/tables/permutation_control.csv` | Null control results (z=9.14) |
| `outputs/tables/depth_robustness.csv` | reps=1,2,3 comparison |
| `outputs/tables/feature_map_comparison.csv` | ZZFeatureMap vs ZFeatureMap |
| `outputs/tables/scalability.csv` | N=50,100,150,200 runtimes |
| `outputs/tables/cross_dataset_results.csv` | sklearn Wine validation |
| `outputs/kernels/K_quantum.npy` | 150×150 quantum kernel matrix |
| `outputs/kernels/K_classical.npy` | 150×150 classical RBF kernel |
| `outputs/RESEARCH_REPORT.md` | Full auto-generated research report |

---

## Launch Dashboard

```powershell
# From the project root:
streamlit run dashboard/app.py
```

---

## Reproducibility

- All random seeds: **42** (sampling, IsolationForest, UMAP)
- Permutation control seeds: **0–9**
- Quantum kernel: deterministic (StatevectorSampler, no shot noise)
- Sample indices saved to: `outputs/tables/sample_indices.npy`

---

## Limitations

1. Quantum computations use classical statevector simulation — **no quantum hardware**
2. Quantum kernel limited to N=150 due to O(N²) computation cost
3. Q-Interestingness weights are heuristically chosen
4. No quantum advantage claimed

---

## Important Scientific Note

> Quantum-specific high-scoring observations are called **"Quantum-specific exploratory candidates"** — not proven anomalies. The framework is exploratory, not a validated anomaly detector.

---

## Citation

If you use this framework for academic work, please cite the dataset sources:
- P. Cortez et al. "Modeling wine preferences by data mining from physicochemical properties." DSS, 2009.
- R.A. Fisher. "The use of multiple measurements in taxonomic problems." Annals of Eugenics, 1936.
