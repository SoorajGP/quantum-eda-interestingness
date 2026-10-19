# Q-Interestingness: Research Notebooks Guide

This directory contains the sequential, reproducible Jupyter notebook suite for the **Q-Interestingness** research framework. Each notebook investigates a specific hypothesis in the transition from classical exploratory data analysis to quantum Hilbert space representations.

---

## Notebook Suite Overview

| Notebook | Title | Core Objective | Key Research Outputs |
| :--- | :--- | :--- | :--- |
| **[01_classical_eda.ipynb](file:///c:/Users/SOORAJ/OneDrive/Desktop/q-interestingness/notebooks/01_classical_eda.ipynb)** | Classical EDA & Baseline Geometry | Establish classical feature distributions, pairwise correlations, PCA, UMAP, and baseline Isolation Forest / LOF anomaly detection. | Preprocessed feature matrices, PCA explained variance ratios, classical anomaly score baseline ($CAS$). |
| **[02_quantum_representation.ipynb](file:///c:/Users/SOORAJ/OneDrive/Desktop/q-interestingness/notebooks/02_quantum_representation.ipynb)** | Feature Encoding & Circuit Architecture | Map scaled features ($[0, \pi]$) to parameterized quantum states using `ZZFeatureMap` (2 repetitions, linear entanglement). | Quantum circuit depth decomposition, parameter assignment, statevector amplitude inspections. |
| **[03_quantum_similarity.ipynb](file:///c:/Users/SOORAJ/OneDrive/Desktop/q-interestingness/notebooks/03_quantum_similarity.ipynb)** | Quantum Fidelity Kernel Evaluation | Construct pairwise state fidelity matrix $K_{ij} = \|\langle\psi(x_i)\|\psi(x_j)\rangle\|^2$ using `StatevectorSampler` and `ComputeUncompute`. | Precomputed quantum kernel $K_q$, PSD eigenvalue verification, off-diagonal concentration statistics. |
| **[04_comparative_analysis.ipynb](file:///c:/Users/SOORAJ/OneDrive/Desktop/q-interestingness/notebooks/04_comparative_analysis.ipynb)** | Comparative Geometry & Classical Controls | Evaluate Centered Kernel Alignment (CKA) against classical RBF, linear, and polynomial kernels; evaluate local $k$-NN Jaccard graph overlaps. | Global CKA ($0.2484$), neighborhood Jaccard at $k \in \{5, 10, 15, 20\}$, kernel divergence benchmark ($D=0.7516$). |
| **[05_q_interestingness.ipynb](file:///c:/Users/SOORAJ/OneDrive/Desktop/q-interestingness/notebooks/05_q_interestingness.ipynb)** | The $QI_{v2}$ Scoring Framework | Formalize Quantum Unusualness ($QU$), Representation Disagreement ($RD$), and composite $QI_{v2}$ scores; profile top exploratory candidates. | Top-13 quantum-specific candidates, component correlation matrix, weight sensitivity analysis ($\lambda \in [0.1, 0.9]$). |
| **[06_validation.ipynb](file:///c:/Users/SOORAJ/OneDrive/Desktop/q-interestingness/notebooks/06_validation.ipynb)** | Experimental Validation & Robustness | Compute 95% bootstrap confidence intervals ($B=1000$), circuit depth ablation ($r=1,2,3$), feature map ablation ($ZZ$ vs $Z$), and synthetic controls. | `FINAL_RESEARCH_RESULTS.csv`, bootstrap CIs, cross-dataset consistency verification. |

---

## Execution Workflow

All notebooks are designed to be run sequentially from top to bottom. You can execute them individually via Jupyter Lab / VS Code or execute the entire headless test harness:

```powershell
# From the repository root:
python run_notebooks.py
```

This harness executes each notebook via `nbconvert` with in-memory execution and writes the updated cells and visual outputs in-place.
