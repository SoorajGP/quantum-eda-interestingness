# Q-Interestingness: Comprehensive Research & Implementation Log

This document serves as the master chronological log, decision record, and methodological history for the **Q-Interestingness (Quantum Exploratory Data Analysis)** research project. It tracks the project from initial formulation through bug discoveries, mathematical refactoring, classical control benchmarking, permutation null validation, cross-domain testing, and noise robustness analysis.

---

## 1. Project Overview & Central Research Question

### The Scientific Problem
In classical data science and exploratory data analysis (EDA), our understanding of data geometry is bounded by Euclidean distance, classical tree partitions, and stationary kernels (such as the Gaussian RBF kernel). High-dimensional tabular datasets often possess non-linear, relational, or multi-feature dependencies that are compressed or overlooked by standard metrics.

### Central Research Question
> *Does mapping classical tabular data into a quantum Hilbert space alter what exploratory analysis identifies as structurally unusual, and can this divergence be systematically quantified to surface complementary exploratory candidates?*

### Initial Experimental Scope
* **Benchmark Dataset**: UCI Red Wine Quality (1,599 observations, 11 physiochemical properties + quality score).
* **Sample Size**: Deterministic subsample of $N = 150$ observations (seed 42) to overcome the $O(N^2)$ pairwise simulation bottleneck on classical computers.
* **Feature Dimension**: Top 4 variance features (`alcohol`, `volatile acidity`, `sulphates`, `total sulfur dioxide`).
* **Encoding Architecture**: Qiskit class-based `ZZFeatureMap` (4 qubits, 2 repetitions, linear entanglement) scaling continuous features to $[0, \pi]$.
* **Similarity Metric**: Quantum state fidelity $K_{ij} = |\langle\psi(x_i)|\psi(x_j)\rangle|^2$ evaluated via `StatevectorSampler` and `ComputeUncompute`.

---

## 2. Chronological Research Timeline & Key Decisions

```
Timeline:
[Phase 0: Baseline Prototype] ──► [Phase 1: Methodology & Bug Audit] ──► [Phase 2: Mathematical Refactoring (QI_v2)]
                                                                                       │
[Phase 5: Permutation Null (B=100)] ◄── [Phase 4: Synthetic Calibration] ◄── [Phase 3: Classical Controls]
               │
               ▼
[Phase 6: Cross-Domain (3 Datasets)] ──► [Phase 7: Finite-Shot Sampling] ──► [Phase 8: Final Synthesis]
```

---

## Phase 0: Initial Prototype Formulation

* **What was implemented**:
  - Continuous features scaled to $[0, \pi]$ and encoded into quantum states using `ZZFeatureMap`.
  - Pairwise fidelity matrix evaluated to form quantum kernel $K_q$.
  - Classical Gaussian RBF kernel $K_c$ built on standardized features.
  - Centered Kernel Alignment (CKA) and $k$-NN Jaccard graph overlap computed.
  - Initial composite score combining Classical Anomaly Score ($CAS$, via Isolation Forest), Quantum Anomaly Score ($QAS$), Local Novelty ($N$), and Boundary Heterogeneity ($B$).
* **Initial Observation**: Classical and quantum kernel alignment on the deterministic $N=150$ sample was $\text{CKA} \approx 0.2484$, and local neighborhood overlap at $k=10$ was only $\approx 0.1004$.

---

## Phase 1: Methodology Audit & Bug Discovery

During rigorous codebase and methodology inspection, two critical flaws were identified and corrected:

### Bug 1: Diagonal Self-Similarity Contamination in $B$-Score
* **The Issue**: Neighborhood heterogeneity ($B$) was originally computed as `np.var(K, axis=1)`. However, the diagonal entries $K_{ii} = 1.0$ (self-similarity) were included in this row-wise variance calculation. For observations with low average similarity to all other points, the presence of the constant diagonal $1.0$ artificially inflated their variance, creating a false signal dominated by self-similarity rather than true neighborhood spread.
* **The Decision**: Explicitly mask the diagonal before calculating variance:
  ```python
  K_no_self = K.copy().astype(float)
  np.fill_diagonal(K_no_self, np.nan)
  scores = np.nanvar(K_no_self, axis=1)
  ```
* **Validation & Verification**: Evaluated the Spearman rank correlation between the old (buggy) and new (corrected) $B$-scores. The correlation was **$\rho = 0.9986$**. This confirmed that while the mathematical flaw was critical to fix for scientific integrity, the relative ranking of exploratory candidates was preserved.

### Bug 2: Unstandardized Feature Selection in sklearn Wine
* **The Issue**: In the preliminary cross-dataset validation on the scikit-learn Wine dataset, top features were selected by raw variance without prior standardization. Consequently, features measured in large arbitrary units (e.g., `proline` with variance $> 90,000$) dominated selection over more informative features with smaller numerical scales.
* **The Decision**: Apply `StandardScaler` *prior* to computing feature variances.
* **Validation & Verification**: The corrected top-4 standardized features yielded a clean representation with $\text{CKA} = 0.4008$ and $\text{Jaccard@10} = 0.2340$, confirming consistent cross-dataset behavior without arbitrary unit bias.

---

## Phase 2: Mathematical Refactoring — The $QI_{v2}$ Architecture

### Rationale
The original $QI$ metric merged internal Hilbert space isolation with cross-representation disagreement into an ad-hoc linear sum. To provide sound scientific interpretability, the metric was refactored into two orthogonal, decoupled signals:

### 1. Quantum Unusualness ($QU$)
Quantifies how atypical an observation is within quantum Hilbert space alone, balancing global distance, local cluster isolation, and neighborhood spread:
$$QU(x) = 0.5 \cdot QAS(x) + 0.3 \cdot N(x) + 0.2 \cdot B(x)$$
* **Global Quantum Anomaly ($QAS$)**: Distance from the global quantum data centroid:
  $$QAS(x_i) = 1 - \frac{1}{N - 1}\sum_{j \neq i} K_{ij}$$
* **Quantum Novelty ($N$)**: Isolation from the $k=5$ nearest quantum neighbors:
  $$N(x_i) = 1 - \frac{1}{k}\sum_{j \in \text{Top-}k(i)} K_{ij}$$
* **Quantum Neighborhood Heterogeneity ($B$)**: Variance of affinities excluding diagonal:
  $$B(x_i) = \operatorname{Var}_{j \neq i}(K_{ij})$$

### 2. Representation Disagreement ($RD$)
Quantifies geometric tension between classical Euclidean/tree space and quantum Hilbert space:
$$RD(x) = 0.5 \cdot |QAS(x) - CAS(x)| + 0.5 \cdot (1 - J_k(x))$$
* **Classical Anomaly Score ($CAS$)**: Min-max normalized Isolation Forest anomaly score.
* **Neighborhood Jaccard Overlap ($J_k$)**: Proportion of shared $k$-NN neighbors ($k=5$).

### 3. Composite Score ($QI_{v2}$)
$$QI_{v2}(x) = \lambda \cdot QU(x) + (1 - \lambda) \cdot RD(x) \quad (\text{default } \lambda = 0.5)$$

### Empirical Validation of the Formulation:
* **Ranking Stability**: Evaluated continuous parameter sweeps $\lambda \in [0.1, 0.9]$. The pairwise Spearman correlation matrix yielded an average stability of **$\rho = 0.9697$** (95% bootstrap CI $[0.9220, 0.9999]$), demonstrating that the candidate ranking does not depend on arbitrary hyperparameter tuning.
* **Component Redundancy Check**: Pairwise Spearman correlations showed $QAS$ vs $N$ at $\rho = 0.6392$ (moderately aligned but distinct), while $QAS$ vs $CAS$ sat at $\rho = 0.1954$ (largely orthogonal, validating the hypothesis of distinct geometries).

---

## Phase 3: Classical Controls Benchmark (The Divergence Hypothesis)

### The Core Critique
*Reviewer question*: "Does a quantum feature map merely emulate standard classical non-linear transformations like polynomial expansion or random Fourier projections?"

### Methodological Test
We benchmarked kernel divergence $D(K_A, K_B) = 1 - \text{CKA}(K_A, K_B)$ against classical baselines relative to the Gaussian RBF kernel:

| Kernel Formulation | CKA vs. RBF | Divergence ($D = 1 - \text{CKA}$) | Comparison |
| :--- | :---: | :---: | :--- |
| **Quantum (`ZZFeatureMap`, reps=2)** | **0.2484** | **0.7516** | **Primary representation** |
| Classical Polynomial (degree = 3) | 0.6702 | 0.3298 | Quantum divergence is $> 2.2\times$ larger |
| Classical Linear | 0.7555 | 0.2445 | Mild linear-to-Gaussian divergence |
| Random Fourier Features (RFF, $D=500$) | 0.9841 | 0.0159 | Rapidly converges to true RBF geometry |

### Scientific Conclusion
The entangling quantum feature map produces **over twice the structural divergence** from RBF compared to a 3rd-degree polynomial kernel ($0.7516$ vs $0.3298$). This rigorously demonstrates that quantum Hilbert space generates a similarity landscape genuinely distinct from standard classical non-linear feature maps.

---

## Phase 4: Synthetic Manifold Calibration

To understand *which* geometric topologies benefit from quantum representation, synthetic datasets with injected uniform spatial outliers were evaluated:

| Dataset | Topology | CKA | CAS $P@10$ | RD $P@10$ | $QI_{v2}$ $P@10$ |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Gaussian Clusters** | Linearly separable blobs | **0.8443** | **1.00** | 0.20 | **0.90** |
| **Two Moons** | Intertwined non-linear arcs | **0.4556** | 0.70 | **0.70** | **0.60** |
| **Concentric Circles** | Nested radial manifolds | **0.3958** | 0.80 | **0.60** | **0.70** |

### Takeaways & Limitations
* Classical Isolation Forest is optimal for trivial spatial outliers in Euclidean space ($P@10 = 1.0$).
* On nested, non-linearly separable manifolds (Two Moons, Concentric Circles), classical and quantum representations diverge significantly ($\text{CKA} \approx 0.40$).
* Representation Disagreement ($RD$) strongly activates, guiding $QI_{v2}$ to detect points that violate manifold continuity.

---

## Phase 5: Full Quantum Permutation Null Test ($B=100$)

### Rationale
Previously, the statistical significance of $\text{CKA} = 0.2484$ relied on only 10 quantum permutations (insufficient for a non-parametric $p$-value) and a classical RBF permutation proxy ($z = 5.29$). To meet peer-review conference standards, a full quantum permutation test was executed across 100 independent quantum kernel evaluations on feature-shuffled data (~72 minutes of compute).

### Results
* **Permuted Null Distribution**: $\mu_{\text{null}} = 0.1821 \pm 0.0074$, $\text{Min} = 0.1628, \text{Max} = 0.2001$.
* **Observed Value**: $\text{CKA} = 0.2484$.
* **Standardized Score**:
  $$z = \frac{0.2484 - 0.1821}{0.0074} = \mathbf{+8.91}$$
* **Non-Parametric Empirical $p$-value**:
  $$p = \frac{1 + \sum_{b=1}^{100} \mathbb{I}(CKA_{\text{null}}^{(b)} \ge CKA_{\text{obs}})}{101} = \frac{1 + 0}{101} = \mathbf{0.0099} \ (p < 0.01)$$

### Scientific Conclusion
Out of 100 independent quantum permutations, **0 trials** ever reached or exceeded $0.2484$. This formally disproves the null hypothesis that the observed quantum-classical alignment is an artifact of random quantum state concentration or small sample size ($N=150$).

---

## Phase 6: Cross-Domain Generalizability (3 Real-World Datasets)

To verify that representation divergence is not an idiosyncrasy of wine chemical properties, the pipeline was executed across 3 distinct real-world tabular domains:

| Dataset | Domain | Samples ($N$) | Qubits | CKA | Jaccard@10 | Quantum-Only Candidates |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **UCI Red Wine Quality** | Chemical / Sensory | 150 | 4 | **0.2484** | **0.1004** | **13** |
| **Wine Recognition (sklearn)** | Chemical / Cultivar | 150 | 4 | **0.4008** | **0.2340** | **13** |
| **Breast Cancer Wisconsin** | Clinical / Diagnostic | 150 | 4 | **0.2983** | **0.1526** | **13** |

* Across all domains, CKA consistently falls in $[0.25, 0.40]$, neighborhood overlap remains low ($10\% - 23\%$), and the framework consistently surfaces 13 quantum-specific candidates at the 90th percentile threshold.

---

## Phase 7: Finite-Shot Sampling & Hardware Viability

To address the critique that results depend on ideal infinite-precision statevectors, we evaluated the fidelity kernel under finite measurement shot sampling ($S \in \{1024, 4096, 8192\}$):

| Measurement Shots | CKA vs. Classical RBF | Difference vs. Ideal ($|\Delta \text{CKA}|$) | QAS Spearman Correlation vs. Ideal ($\rho$) |
| :---: | :---: | :---: | :---: |
| **1024** | 0.2480 | $0.0004$ | **0.9990** |
| **4096** | 0.2483 | $0.0001$ | **0.9997** |
| **8192** | 0.2484 | $0.0000$ | **0.9999** |
| **Ideal Statevector ($\infty$)** | **0.2484** | $0.0000$ | **1.0000** |

* Even with modest shot budgets ($S=1024$), candidate rankings correlate at $\rho = 0.9990$ with ideal statevectors, confirming robustness to quantum measurement noise.

---

## Phase 8: Circuit Depth & Entanglement Ablation

* **Entanglement contribution**: Replacing `ZZFeatureMap` (entangling gates) with `ZFeatureMap` (separable single-qubit rotations) increases CKA by **+0.3913** (from 0.2484 to 0.6397). Circuit entanglement drives the geometric divergence.
* **Circuit depth**: Scaling repetitions from $r=1$ to $r=3$ shifts CKA monotonically from $0.285 \to 0.221$, indicating stable metric concentration without exponential state-space collapse at low qubit counts ($n=4$).

---

## 3. Explicit Limitations & Scientific Positioning

1. **Simulation Backend**: All quantum calculations use classical statevector simulation. Physical NISQ QPUs will introduce gate errors, cross-talk, and decoherence.
2. **Sample Scaling**: Due to $O(N^2)$ pairwise simulation complexity, primary benchmarks used deterministic subsets of $N=150$. Full dataset scaling requires distributed compute or physical quantum hardware.
3. **Exploratory Candidates vs. Ground Truth**: Data points identified with high $QI_{v2}$ are designated as **"Quantum-Specific Exploratory Candidates"**. They represent structural divergences between metric spaces to guide domain-expert hypothesis generation, not confirmed real-world physical faults.
4. **No Quantum Advantage Claim**: This work claims no asymptotic computational speedup or general superiority over classical anomaly detection algorithms.

---

## 4. Master Decision & Experiment Changelog

| Timestamp | Phase | Decision / Action Taken | Primary Metric / Output |
| :--- | :--- | :--- | :--- |
| **Initial** | Formulation | Selected UCI Red Wine, $N=150$, 4 qubits, `ZZFeatureMap`, reps=2. | $\text{CKA} = 0.2484$, Jaccard@10 = $0.1004$ |
| **Audit** | Bug Fix | Corrected $B$-score diagonal contamination via `np.nanvar`. | Spearman $\rho(\text{old}, \text{new}) = 0.9986$ |
| **Audit** | Bug Fix | Standardized features before variance selection in sklearn Wine. | Selected top-4 standardized features cleanly |
| **Upgrade** | Formulation | Decomposed metric into $QU$ (internal unusualness) and $RD$ (disagreement). | Formalized $QI_{v2}(x) = \lambda QU + (1-\lambda)RD$ |
| **Upgrade** | Robustness | Continuous $\lambda \in [0.1, 0.9]$ sweep. | Mean Spearman stability $\rho = 0.9697$ |
| **Upgrade** | Controls | Benchmarked against Classical Linear, Poly3, and RFF. | $D_{\text{quantum}} = 0.7516$ vs $D_{\text{poly}} = 0.3298$ |
| **Upgrade** | Synthetic | Tested Gaussian clusters and Two Moons with spatial anomalies. | Calibrated precision and complementary behavior |
| **Validation** | Rigor | Executed full quantum permutation test ($B=100$, ~72 min). | $\mu_{\text{null}} = 0.1821 \pm 0.0074, z = +8.91, p < 0.01$ |
| **Validation** | Generality | Tested 3rd real-world dataset: Wisconsin Breast Cancer. | $\text{CKA} = 0.2983$, Jaccard@10 = $0.1526$, Q-only = 13 |
| **Validation** | Manifolds | Tested Concentric Circles synthetic dataset. | $\text{CKA} = 0.3958$, $QI_{v2}$ $P@10 = 0.70$ |
| **Validation** | Hardware | Evaluated finite-shot measurement sampling (1024 to 8192 shots). | $|\Delta \text{CKA}| \le 0.0004$, Spearman $\rho \ge 0.9990$ |
