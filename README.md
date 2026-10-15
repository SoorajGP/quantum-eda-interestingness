# Q-Interestingness: Quantum Exploratory Data Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 2.5.2](https://img.shields.io/badge/Qiskit-2.5.2-613394.svg)](https://qiskit.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Research](https://img.shields.io/badge/Status-Research%20Prototype-informational.svg)]()

> **Central Research Question**: *Does mapping classical tabular data into a quantum Hilbert space alter what exploratory analysis identifies as structurally unusual, and can this divergence be systematically quantified to surface complementary exploratory candidates?*

---

## Overview

In classical exploratory data analysis (EDA) and anomaly detection, our perception of structure is bounded by Euclidean distance, classical density estimators, and stationary kernels (such as the Gaussian RBF kernel). 

**Q-Interestingness** investigates whether parameterized quantum circuits—specifically entangling quantum feature maps—induce an alternative geometric representation that reveals non-trivial structural relationships invisible to classical tools. By embedding classical features into quantum states via non-linear phase rotations and multi-qubit entanglement, data points are projected onto a high-dimensional state space where inner product fidelity serves as a similarity metric.

This repository provides an end-to-end experimental framework to:
1. **Quantify structural divergence** between classical and quantum kernel representations using Centered Kernel Alignment (CKA) and local neighborhood graph overlaps.
2. **Benchmark against classical non-linear controls** (polynomial and random Fourier feature kernels) to test whether quantum divergence is distinct from standard non-linear transformations.
3. **Formalize the Q-Interestingness ($QI_{v2}$) score**, decoupling internal quantum unusualness from cross-representation disagreement.
4. **Identify quantum-specific exploratory candidates**—data points that appear typical in classical feature space but exhibit marked isolation or relational heterogeneity in quantum state space.

---

## Key Empirical Findings

All primary metrics were evaluated on the **UCI Red Wine Quality** dataset ($N=150$ deterministic subsample, 4 principal features mapped to 4 qubits via `ZZFeatureMap` with linear entanglement and depth $r=2$):

| Metric | Value | 95% Bootstrap CI | Scientific Interpretation |
| :--- | :---: | :---: | :--- |
| **Classical–Quantum CKA** | **0.2484** | $[0.3132, 0.3851]$ | Substantial divergence from classical Gaussian RBF geometry ($1 - \text{CKA} = 0.7516$). |
| **Neighborhood Jaccard Overlap ($k=10$)** | **0.1004** | $[0.0883, 0.1138]$ | Approximately 90% of a sample's nearest neighbors change when moving to quantum space. |
| **Top-10 Anomaly Agreement** | **0.20** | — | Weak overlap between classical Isolation Forest outliers and quantum anomaly rankings. |
| **Quantum-Specific Candidates** | **13 / 150** | — | Observations surfaced as high-interest candidates uniquely by the quantum metric. |
| **$QI_{v2}$ Rank Stability (Spearman)** | **0.9697** | $[0.9220, 0.9999]$ | Relative candidate rankings remain robust across component weight configurations. |

### Quantum Divergence vs. Classical Controls

A key methodological question is whether quantum feature maps simply emulate standard classical non-linearities. To test this, we compared kernel divergence $D(K_A, K_B) = 1 - \text{CKA}(K_A, K_B)$ against classical baselines relative to the RBF kernel:

| Kernel Formulation | Divergence vs. Classical RBF ($D$) | Relative Difference |
| :--- | :---: | :--- |
| **Quantum (`ZZFeatureMap`, reps=2)** | **0.7516** | **Primary representation** |
| Classical Polynomial (degree = 3) | 0.3298 | Diverges by less than half of quantum |
| Classical Linear | 0.2445 | Mild linear-to-Gaussian divergence |
| Random Fourier Features (RFF, $D=500$) | 0.0159 | Converges closely to true RBF |

The quantum feature map produces **over twice the structural divergence** from RBF compared to a 3rd-degree polynomial kernel, confirming that the quantum Hilbert space creates a genuinely distinct similarity landscape rather than a trivial non-linear perturbation.

---

## Mathematical Framework: $QI_{v2}$

The Q-Interestingness framework maps feature vectors $x \in \mathbb{R}^d$ into quantum states, builds a fidelity kernel, and computes a composite interest score composed of two complementary signals.

```
                           Classical Features (x)
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 Classical Representation                             Quantum Representation
   • Euclidean / RBF Geometry                           • Feature map U_Φ(x)
   • Isolation Forest (CAS)                             • Fidelity Kernel K_ij
           │                                                   │
           │                                                   ├─ Global Anomaly (QAS)
           │                                                   ├─ Local Novelty (N)
           │                                                   └─ Heterogeneity (B)
           │                                                           │
           │                                                           ▼
           │                                                Quantum Unusualness (QU)
           │                                                           │
           └─────────────────────────┬─────────────────────────────────┘
                                     ▼
                     Representation Disagreement (RD)
                                     │
                                     ▼
                      Composite Q-Interestingness (QI_v2)
```

### 1. Quantum State Encoding & Kernel Evaluation

Features are normalized to $[0, \pi]$ and encoded using Qiskit's class-based `ZZFeatureMap` (2 repetitions, linear entanglement):

$$|\psi(x)\rangle = U_{\Phi(x)}|0\rangle^{\otimes n}, \quad U_{\Phi(x)} = \exp\left(i \sum_{j=1}^n x_j Z_j + \sum_{j < k} (\pi - x_j)(\pi - x_k) Z_j Z_k\right)$$

The quantum kernel similarity between two observations is given by the state fidelity:

$$K_{ij} = |\langle\psi(x_i)|\psi(x_j)\rangle|^2$$

Computed using `StatevectorSampler` and `ComputeUncompute` from `qiskit_machine_learning`.

---

### 2. Quantum Unusualness ($QU$)

Measures how atypical an observation is within the quantum feature space alone, balancing global isolation, local novelty, and neighborhood variance:

$$QU(x) = 0.5 \cdot QAS(x) + 0.3 \cdot N(x) + 0.2 \cdot B(x)$$

* **Quantum Anomaly Score ($QAS$)**: Global distance in Hilbert space:
  $$QAS(x_i) = 1 - \frac{1}{N - 1}\sum_{j \neq i} K_{ij}$$
* **Quantum Novelty ($N$)**: Local isolation from the top-$k$ nearest quantum neighbors ($k=5$):
  $$N(x_i) = 1 - \frac{1}{k}\sum_{j \in \text{Top-}k(i)} K_{ij}$$
* **Quantum Neighborhood Heterogeneity ($B$)**: Variance of pairwise kernel affinities with all other observations, explicitly excluding the self-similarity diagonal:
  $$B(x_i) = \operatorname{Var}_{j \neq i}(K_{ij})$$

---

### 3. Representation Disagreement ($RD$)

Quantifies the tension between classical and quantum representations, highlighting points where classical and quantum models disagree on geometry:

$$RD(x) = 0.5 \cdot |QAS(x) - CAS(x)| + 0.5 \cdot (1 - J_k(x))$$

* **Classical Anomaly Score ($CAS$)**: Min-max normalized anomaly score obtained from an Isolation Forest fitted on classical features.
* **Neighborhood Jaccard Overlap ($J_k$)**: Degree of shared nearest neighbors between classical Euclidean space and quantum kernel space ($k=5$):
  $$J_k(x_i) = \frac{|\mathcal{N}_{\text{classical}}^{(k)}(x_i) \cap \mathcal{N}_{\text{quantum}}^{(k)}(x_i)|}{|\mathcal{N}_{\text{classical}}^{(k)}(x_i) \cup \mathcal{N}_{\text{quantum}}^{(k)}(x_i)|}$$

---

### 4. Composite Metric ($QI_{v2}$)

The composite score balances internal quantum structure with cross-representation disagreement:

$$QI_{v2}(x) = \lambda \cdot QU(x) + (1 - \lambda) \cdot RD(x) \quad (\text{default } \lambda = 0.5)$$

---

## Experimental Validation & Controls

### Cross-Dataset Validation

To verify that the structural divergence generalizes beyond a single dataset, the identical pipeline was evaluated on both UCI Red Wine Quality and the scikit-learn Wine dataset (with standardized top-variance features):

| Dataset | Sample Size | CKA (Quantum vs. RBF) | Jaccard@10 | Quantum-Only Candidates |
| :--- | :---: | :---: | :---: | :---: |
| **Red Wine Quality (UCI)** | 150 | **0.2484** | **0.1004** | **13** |
| **Wine Recognition (sklearn)** | 150 | **0.4008** | **0.2340** | **13** |

### Feature Map & Depth Ablation

* **Entanglement contribution**: Replacing `ZZFeatureMap` (with 2-qubit entangling gates) with `ZFeatureMap` (separable single-qubit rotations only) increases CKA by **+0.3913** (from 0.2484 to 0.6397). This demonstrates that circuit entanglement, rather than single-qubit phase rotation alone, drives the geometric divergence.
* **Circuit depth**: Scaling repetitions from $r=1$ to $r=3$ shifts CKA monotonically from $0.285 \to 0.221$, indicating stable metric concentration without exponential state-space collapse at low qubit counts ($n=4$).

### Synthetic Sanity Checks

Synthetic datasets (Gaussian clusters and Two Moons with injected uniform spatial outliers) were analyzed to calibrate expectations:
* Classical Isolation Forest identifies spatial outliers reliably ($\text{Precision@10} = 1.0$).
* $QI_{v2}$ achieves $\text{Precision@10} = 0.90$ on Gaussian and $0.60$ on Two Moons.
* **Takeaway**: Classical methods remain optimal for simple spatial outliers in low-dimensional Euclidean space. Quantum feature maps are not intended to replace classical anomaly detection for standard geometric outliers; rather, they serve as a lens for non-linear, relational patterns that classical metrics compress.

---

## Repository Structure

```
q-interestingness/
├── src/
│   ├── data.py              # Dataset acquisition, standardization, sampling
│   ├── classical.py         # PCA, UMAP, Isolation Forest, LOF, RBF kernels
│   ├── quantum.py           # ZZFeatureMap, FidelityQuantumKernel (Qiskit 2.5.2)
│   ├── metrics.py           # CKA, Jaccard neighborhoods, anomaly overlaps
│   └── interestingness.py   # QAS, Novelty, Heterogeneity, QU, RD, and QI_v2
├── notebooks/
│   ├── 01_classical_eda.ipynb          # Classical baseline distributions and embeddings
│   ├── 02_quantum_representation.ipynb # Feature encoding and circuit inspection
│   ├── 03_quantum_similarity.ipynb     # Kernel matrix evaluation and statevector checks
│   ├── 04_comparative_analysis.ipynb   # CKA, neighborhood divergence, and controls
│   ├── 05_q_interestingness.ipynb      # QI_v2 scoring and candidate profiling
│   └── 06_validation.ipynb             # Bootstrap CIs, ablations, and synthetic checks
├── dashboard/
│   └── app.py               # Interactive Streamlit dashboard
├── outputs/
│   ├── figures/             # High-resolution publication plots
│   ├── tables/              # Exported CSV result tables and bootstrap metrics
│   ├── kernels/             # Precomputed kernel matrices (.npy)
│   ├── RESEARCH_REPORT.md   # Detailed experimental findings
│   └── FINAL_RESEARCH_AUDIT.md # Audit log of verified calculations
├── upgrade.py               # End-to-end upgrade pipeline script
├── generate_audit.py        # Verification and consistency audit script
├── generate_final_outputs.py# Summary tables and final report generator
└── requirements.txt         # Pinned project dependencies
```

---

## Quick Start

### 1. Environment Setup

Clone the repository and install dependencies in a clean virtual environment:

```bash
git clone https://github.com/SoorajGP/quantum-eda-interestingness.git
cd quantum-eda-interestingness

python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run the Research Pipeline

Execute the full analysis pipeline to compute kernel matrices, run bootstrap validation, and generate summary tables:

```bash
# Run metrics upgrade pipeline
python upgrade.py

# Generate audit and consistency reports
python generate_audit.py
python generate_final_outputs.py
```

### 3. Launch the Interactive Dashboard

An interactive Streamlit application is included for visual exploration of the quantum vs. classical representations:

```bash
streamlit run dashboard/app.py
```

The dashboard allows you to:
- Adjust anomaly percentile thresholds and inspect top-$N$ ranked observations.
- Filter data points by category (`Quantum-only`, `Classical-only`, `Both`, `Neither`).
- Inspect Kernel PCA projections and kernel heatmaps side-by-side.
- Analyze individual candidate feature profiles against bulk distributions.

---

## Scientific Positioning & Limitations

To ensure sound scientific practice, the scope and assumptions of this research are explicitly stated:

1. **Simulation Backend**: All quantum calculations use classical statevector simulation via Qiskit's `StatevectorSampler` and `ComputeUncompute`. No physical quantum processing units (QPUs) were used. Real quantum hardware execution will introduce gate noise and readout error, which may affect kernel concentration.
2. **Sample Scaling**: Due to the $O(N^2)$ computational complexity of pairwise state fidelity simulation, primary experiments used deterministic subsets of $N=150$. Full dataset scaling ($N > 1000$) requires distributed simulation or quantum hardware execution.
3. **Exploratory Candidates vs. Physical Ground Truth**: Data points identified with high $QI_{v2}$ scores are designated as **"Quantum-Specific Exploratory Candidates"**. They represent structural divergences between metric spaces to guide domain-expert hypothesis generation, not confirmed real-world faults or ground-truth anomalies.
4. **No Quantum Advantage Claim**: This work claims no asymptotic computational speedup or general superiority over classical anomaly detection algorithms. The contribution is a formal framework for representation-dependent exploratory data analysis.

---

## Citation

If you find this work or codebase helpful in your research, please cite:

```bibtex
@software{q_interestingness_2026,
  author = {Sooraj G P},
  title = {Q-Interestingness: Quantum Exploratory Data Analysis for Discovering Hidden Structure and Anomalies},
  year = {2026},
  url = {https://github.com/SoorajGP/quantum-eda-interestingness}
}
```

---

## License

This project is licensed under the [MIT License](LICENSE).
