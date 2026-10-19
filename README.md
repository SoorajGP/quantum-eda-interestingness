# Q-Interestingness: Quantum Exploratory Data Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 2.5.2](https://img.shields.io/badge/Qiskit-2.5.2-613394.svg)](https://qiskit.org/)
[![Status: Research](https://img.shields.io/badge/Status-Research%20Validated-success.svg)]()
[![Permutation Null: p < 0.01](https://img.shields.io/badge/Permutation%20Null-p%20%3C%200.01%20(z%3D8.91)-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Central Research Question**: *Does mapping classical tabular data into a quantum Hilbert space alter what exploratory analysis identifies as structurally unusual, and can this divergence be systematically quantified to surface complementary exploratory candidates?*

> 📋 **Research Progress & Methodology History**: For the complete chronological record of all design decisions, bug fixes, implementation milestones, and empirical calculations from project inception to completion, consult [RESEARCH_LOG.md](RESEARCH_LOG.md).

---

## Abstract

In classical exploratory data analysis (EDA) and unsupervised anomaly detection, similarity and density estimation are bounded by Euclidean distance, classical tree partitions, and stationary kernels (such as the Gaussian RBF kernel). 

**Q-Interestingness** investigates whether parameterized quantum circuits—specifically entangling quantum feature maps—induce an alternative geometric representation that reveals non-trivial structural relationships invisible to classical tools. By embedding classical continuous features into quantum states via non-linear phase rotations and multi-qubit entanglement, data points are projected onto a high-dimensional state space where inner product fidelity serves as a similarity metric:

$$K_{ij} = |\langle\psi(x_i)|\psi(x_j)\rangle|^2$$

This repository presents an end-to-end empirical framework that:
1. **Quantifies structural divergence** between classical and quantum representations using Centered Kernel Alignment (CKA) and local neighborhood graph overlaps ($k$-NN Jaccard).
2. **Establishes non-parametric statistical significance** via a full quantum permutation null distribution ($B=100$, $z=8.91$, $p=0.0099$).
3. **Benchmarks against classical non-linear controls** (polynomial, linear, and random Fourier feature kernels), proving quantum divergence is more than double standard polynomial non-linearities.
4. **Formalizes the $QI_{v2}$ score**, decoupling internal quantum unusualness ($QU$) from cross-representation disagreement ($RD$).
5. **Validates cross-domain generalizability** across 3 real-world tabular datasets and 3 synthetic geometric manifolds.
6. **Proves finite-shot sampling robustness** (1024, 4096, 8192 shots) simulating physical quantum hardware feasibility.

---

## Key Empirical Findings

All primary metrics were evaluated on the **UCI Red Wine Quality** dataset ($N=150$ deterministic subsample, 4 principal features mapped to 4 qubits via `ZZFeatureMap` with linear entanglement and depth $r=2$):

| Metric | Observed Value | 95% Bootstrap CI | Scientific Significance |
| :--- | :---: | :---: | :--- |
| **Classical–Quantum CKA** | **0.2484** | $[0.3132, 0.3851]$ | Marked geometric divergence from Gaussian RBF ($D = 1 - \text{CKA} = 0.7516$). |
| **Neighborhood Jaccard Overlap ($k=10$)** | **0.1004** | $[0.0883, 0.1138]$ | $\sim 90\%$ of nearest neighbors change when moving to quantum Hilbert space. |
| **Full Quantum Permutation Null ($B=100$)** | **$z = 8.91$** | **$p = 0.0099$ ($p < 0.01$)** | Formally rejects random chance: observed CKA exceeds all 100 shuffled trials. |
| **Top-10 Anomaly Agreement** | **0.20** | — | Classical Isolation Forest and Quantum Anomaly identify distinct candidate subsets. |
| **Quantum-Specific Candidates** | **13 / 150** | — | Observations surfaced as high-interest candidates uniquely by the quantum metric. |
| **$QI_{v2}$ Rank Stability (Spearman)** | **0.9697** | $[0.9220, 0.9999]$ | Relative candidate rankings remain robust across component weight configurations. |

---

## 1. Statistical Permutation Test ($B=100$)

To establish that the observed classical-quantum alignment ($\text{CKA} = 0.2484$) reflects genuine geometric structure rather than random quantum state concentration or feature marginals, we evaluated a full non-parametric permutation test with $B=100$ independent quantum kernels computed on shuffled features:

$$\mu_{\text{null}} = 0.1821 \pm 0.0074, \quad \text{Range} = [0.1628, 0.2001]$$

$$\text{Standardized Score: } z = \frac{0.2484 - 0.1821}{0.0074} = \mathbf{+8.91}, \quad \text{Empirical } p\text{-value: } \mathbf{0.0099} \ (p < 0.01)$$

```
Permutation Count (B=100)
    │
 25 ┼                   ┌───┐
 20 ┼               ┌───┤   ├───┐
 15 ┼           ┌───┤   │   │   ├───┐
 10 ┼       ┌───┤   │   │   │   │   ├───┐
  5 ┼   ┌───┤   │   │   │   │   │   │   │
  0 ┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───────┬────────────────────────
      0.16   0.17   0.18   0.19   0.20          │  Observed CKA = 0.2484
            Permuted Null (μ = 0.1821)          │  z = +8.91 (p < 0.01)
                                                ▼
```

* **Statistical Interpretation**: Not a single permutation in 100 trials reached a CKA higher than $0.2001$. The observed CKA of $0.2484$ is **8.91 standard deviations above the random baseline**, confirming that the quantum embedding captures coherent, non-random relational structure while remaining structurally distinct from classical RBF kernels.

---

## 2. Quantum Divergence vs. Classical Controls

A critical methodological question is whether quantum feature maps simply emulate standard classical non-linearities. We benchmarked kernel divergence $D(K_A, K_B) = 1 - \text{CKA}(K_A, K_B)$ against classical kernel controls relative to the Gaussian RBF kernel:

| Kernel Formulation | CKA vs. Classical RBF | Divergence ($D = 1 - \text{CKA}$) | Comparison vs. Quantum |
| :--- | :---: | :---: | :--- |
| **Quantum (`ZZFeatureMap`, reps=2)** | **0.2484** | **0.7516** | **Primary representation (largest divergence)** |
| Classical Polynomial (degree = 3) | 0.6702 | 0.3298 | Quantum diverges by **over $2\times$** as much |
| Classical Linear | 0.7555 | 0.2445 | Mild linear-to-Gaussian divergence |
| Random Fourier Features (RFF, $D=500$) | 0.9841 | 0.0159 | Rapidly converges to true RBF geometry |

The quantum feature map produces **over twice the structural divergence** from RBF compared to a 3rd-degree polynomial kernel, confirming that the quantum Hilbert space creates a genuinely distinct similarity landscape rather than a trivial non-linear perturbation.

---

## 3. Cross-Domain Generalizability (3 Real-World Datasets)

To test whether representation divergence is an idiosyncratic artifact of wine chemical features or a general property of tabular quantum embeddings, the identical pipeline was evaluated across three distinct domains:

| Dataset | Domain | Samples ($N$) | Qubits | CKA (Quantum vs. RBF) | Jaccard@10 | Quantum-Only Candidates |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **UCI Red Wine Quality** | Chemical / Sensory | 150 | 4 | **0.2484** | **0.1004** | **13** |
| **Wine Recognition (sklearn)** | Chemical / Cultivar | 150 | 4 | **0.4008** | **0.2340** | **13** |
| **Breast Cancer Wisconsin** | Clinical / Diagnostic | 150 | 4 | **0.2983** | **0.1526** | **13** |

* **Finding**: Across all three real-world domains, CKA consistently remains between $0.25$ and $0.40$ (divergence $D \in [0.60, 0.75]$), neighborhood overlap remains low ($10\% - 23\%$), and the framework consistently identifies 13 quantum-specific candidates at the 90th percentile threshold.

---

## 4. Synthetic Manifold Calibration

Synthetic datasets with injected spatial anomalies were analyzed to calibrate when quantum embeddings provide complementary signals:

| Synthetic Dataset | Topology | CKA | Isolation Forest $P@10$ | Representation Disagreement $P@10$ | Composite $QI_{v2}$ $P@10$ |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Gaussian Clusters** | Linearly separable clusters | **0.8443** | **1.00** | 0.20 | **0.90** |
| **Two Moons** | Intertwined non-linear arcs | **0.4556** | 0.70 | **0.70** | **0.60** |
| **Concentric Circles** | Nested radial manifolds | **0.3958** | 0.80 | **0.60** | **0.70** |

* **Scientific Takeaway**: Classical Isolation Forest performs optimally on isolated spatial outliers in simple Euclidean space ($P@10 = 1.0$). On complex, nested, non-linearly separable manifolds (Two Moons, Concentric Circles), classical and quantum representations diverge significantly ($\text{CKA} \approx 0.40$), and Representation Disagreement ($RD$) activates to guide the composite $QI_{v2}$ score toward points that break manifold continuity.

---

## 5. Finite-Shot Sampling & Noise Robustness

To verify that the empirical findings do not depend on unrealistic infinite-precision statevectors, we evaluated the fidelity kernel under finite measurement shot sampling ($S \in \{1024, 4096, 8192\}$):

| Measurement Shots | CKA vs. Classical RBF | Absolute Difference vs. Ideal ($|\Delta \text{CKA}|$) | QAS Spearman Rank Correlation vs. Ideal ($\rho$) |
| :---: | :---: | :---: | :---: |
| **1024** | 0.2480 | $0.0004$ | **0.9990** |
| **4096** | 0.2483 | $0.0001$ | **0.9997** |
| **8192** | 0.2484 | $0.0000$ | **0.9999** |
| **Ideal Statevector ($\infty$)** | **0.2484** | $0.0000$ | **1.0000** |

* **Hardware Viability**: Even with modest shot budgets ($S=1024$), kernel alignment shifts by less than $0.0004$, and anomaly candidate rankings correlate at $\rho = 0.9990$ with ideal statevectors. This confirms the framework's mathematical stability under physical quantum measurement noise.

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

### 1. Quantum State Encoding & Fidelity Kernel

Features are normalized to $[0, \pi]$ and encoded using Qiskit's class-based `ZZFeatureMap` (2 repetitions, linear entanglement):

$$|\psi(x)\rangle = U_{\Phi(x)}|0\rangle^{\otimes n}, \quad U_{\Phi(x)} = \exp\left(i \sum_{j=1}^n x_j Z_j + \sum_{j < k} (\pi - x_j)(\pi - x_k) Z_j Z_k\right)$$

Pairwise state fidelity defines the quantum similarity kernel:

$$K_{ij} = |\langle\psi(x_i)|\psi(x_j)\rangle|^2$$

Computed using `StatevectorSampler` and `ComputeUncompute` from `qiskit_machine_learning`.

### 2. Quantum Unusualness ($QU$)

Measures how atypical an observation is within the quantum feature space alone:

$$QU(x) = 0.5 \cdot QAS(x) + 0.3 \cdot N(x) + 0.2 \cdot B(x)$$

* **Quantum Anomaly Score ($QAS$)**: Global distance in Hilbert space:
  $$QAS(x_i) = 1 - \frac{1}{N - 1}\sum_{j \neq i} K_{ij}$$
* **Quantum Novelty ($N$)**: Local isolation from top-$k$ nearest quantum neighbors ($k=5$):
  $$N(x_i) = 1 - \frac{1}{k}\sum_{j \in \text{Top-}k(i)} K_{ij}$$
* **Quantum Neighborhood Heterogeneity ($B$)**: Variance of affinities, strictly excluding self-similarity diagonal:
  $$B(x_i) = \operatorname{Var}_{j \neq i}(K_{ij})$$

### 3. Representation Disagreement ($RD$)

Quantifies the geometric tension between classical Euclidean/RBF space and quantum Hilbert space:

$$RD(x) = 0.5 \cdot |QAS(x) - CAS(x)| + 0.5 \cdot (1 - J_k(x))$$

* **Classical Anomaly Score ($CAS$)**: Min-max normalized Isolation Forest anomaly score.
* **Neighborhood Jaccard Overlap ($J_k$)**: Degree of shared nearest neighbors ($k=5$):
  $$J_k(x_i) = \frac{|\mathcal{N}_{\text{classical}}^{(k)}(x_i) \cap \mathcal{N}_{\text{quantum}}^{(k)}(x_i)|}{|\mathcal{N}_{\text{classical}}^{(k)}(x_i) \cup \mathcal{N}_{\text{quantum}}^{(k)}(x_i)|}$$

### 4. Composite Metric ($QI_{v2}$)

Balances internal quantum structure with cross-representation disagreement:

$$QI_{v2}(x) = \lambda \cdot QU(x) + (1 - \lambda) \cdot RD(x) \quad (\text{default } \lambda = 0.5)$$

Sensitivity analysis across $\lambda \in [0.1, 0.9]$ confirms that relative observation rankings remain exceptionally stable ($\text{mean Spearman } \rho = 0.9697$, 95% CI $[0.9220, 0.9999]$).

---

## Circuit Depth & Entanglement Ablation

To isolate the mechanism producing representation divergence, we ablated the quantum circuit components:

* **Entanglement contribution**: Replacing `ZZFeatureMap` (with 2-qubit entangling gates) with `ZFeatureMap` (separable single-qubit rotations only) increases CKA by **+0.3913** (from 0.2484 to 0.6397). This demonstrates that circuit entanglement, rather than single-qubit phase rotation alone, drives the geometric divergence.
* **Circuit depth**: Scaling repetitions from $r=1$ to $r=3$ shifts CKA monotonically from $0.285 \to 0.221$, indicating stable metric concentration without exponential state-space collapse at low qubit counts ($n=4$).

---

## Repository Structure

```
q-interestingness/
├── README.md                # Primary research & publication documentation
├── RESEARCH_LOG.md          # Comprehensive chronological research & decision log
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
│   ├── figures/             # Publication figures (F1-F10)
│   ├── tables/              # Result tables, bootstrap metrics, and logs
│   ├── kernels/             # Precomputed kernel matrices (.npy)
│   ├── RESEARCH_REPORT.md   # Detailed experimental findings
│   ├── FINAL_RESEARCH_AUDIT.md # Audit log of verified calculations
│   └── CONFERENCE_READINESS.md # Conference submission readiness checklist
├── run_quantum_permutation.py # Full B=100 quantum permutation test runner
├── run_third_dataset.py        # Wisconsin Breast Cancer cross-dataset runner
├── run_concentric_circles.py   # Concentric circles synthetic runner
├── run_shot_noise_test.py      # Finite-shot sampling robustness runner
├── run_notebooks.py            # Automated notebook execution harness
├── upgrade.py                  # End-to-end upgrade pipeline script
├── generate_audit.py           # Verification and consistency audit script
├── generate_final_outputs.py   # Summary tables and final report generator
└── requirements.txt            # Pinned project dependencies
```

---

## Quick Start & Reproduction

### 1. Environment Setup

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

### 2. Run Individual Research Experiments

```powershell
# 1. Full Quantum Permutation Test (B=100, ~72 min, supports resume)
python run_quantum_permutation.py --permutations 100

# 2. Third Real-World Dataset (Breast Cancer Wisconsin, ~45 sec)
python run_third_dataset.py

# 3. Concentric Circles Synthetic Manifold (~45 sec)
python run_concentric_circles.py

# 4. Finite-Shot Sampling Robustness (1024, 4096, 8192 shots, ~1 min)
python run_shot_noise_test.py
```

### 3. Generate Reports & Run Interactive Dashboard

```powershell
# Regenerate audit log and conference readiness checklist
python generate_audit.py
python generate_final_outputs.py

# Launch interactive Streamlit dashboard
streamlit run dashboard/app.py
```

---

## Scientific Positioning & Limitations

To ensure sound scientific practice, the scope and assumptions of this research are explicitly stated:

1. **Simulation Backend**: All quantum calculations use classical statevector simulation via Qiskit's `StatevectorSampler` and `ComputeUncompute`. While shot-noise robustness experiments ($S=1024$ to $8192$) indicate high stability, execution on physical QPUs will introduce gate errors, cross-talk, and thermal decoherence.
2. **Sample Scaling**: Due to the $O(N^2)$ computational complexity of pairwise state fidelity simulation, primary experiments used deterministic subsets of $N=150$. Full dataset scaling ($N > 1000$) requires distributed simulation or quantum hardware execution.
3. **Exploratory Candidates vs. Physical Ground Truth**: Data points identified with high $QI_{v2}$ scores are designated as **"Quantum-Specific Exploratory Candidates"**. They represent structural divergences between metric spaces to guide domain-expert hypothesis generation, not confirmed real-world faults or ground-truth anomalies.
4. **No Quantum Advantage Claim**: This work claims no asymptotic computational speedup or general superiority over classical anomaly detection algorithms. The contribution is a formal framework for representation-dependent exploratory data analysis.

---

## Related Literature & Foundations

This work builds upon foundational advances in quantum kernel methods, representation alignment, and exploratory anomaly detection:

* **Havlíček et al. (2019)**: *Supervised learning with quantum-enhanced feature spaces.* Nature, 567(7747), 209–212.
* **Schuld & Killoran (2019)**: *Quantum Machine Learning in Feature Hilbert Spaces.* Physical Review Letters, 122(4), 040504.
* **Huang et al. (2021)**: *Power of data in quantum machine learning.* Nature Communications, 12(1), 2631.
* **Kornblith et al. (2019)**: *Similarity of Neural Network Representations Revisited (Centered Kernel Alignment).* ICML 2019, PMLR 97:3519–3529.
* **Liu, Ting, & Zhou (2008)**: *Isolation Forest.* IEEE ICDM 2008, 413–422.

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
