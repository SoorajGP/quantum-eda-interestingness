# Q-Interestingness: Quantum Exploratory Data Analysis
## Research Report — Auto-generated from Experimental Results

---

## 1. Abstract

This report presents experimental results for the Q-Interestingness framework applied to the
UCI Red Wine Quality dataset (N=1,599; quantum computation on N=150 subsample, seed=42) and
validated on the sklearn Wine dataset (N=178). The framework examines whether quantum feature
spaces (ZZFeatureMap + FidelityQuantumKernel via StatevectorSampler) provide complementary
exploratory information relative to classical EDA.

**Key measured values:**
- Classical–Quantum Kernel Alignment (CKA): 0.248383
- Neighborhood Jaccard overlap (k=10): 0.1004 ± 0.0799
- Top-10 anomaly overlap: 0.2000
- Quantum-specific exploratory candidates (N=150): 13
- Q-Interestingness rank stability (Spearman): 0.7977
- Permutation control z-score: 9.14

**Conclusion category: A — Strong evidence of complementary quantum exploratory structure**

---

## 2. Research Question

> Does moving data from a classical feature space into a quantum feature space change what
> exploratory analysis considers structurally unusual, and can this difference be quantified
> through a Q-Interestingness framework?

---

## 3. Hypotheses

| ID | Hypothesis | Measured Value | Supported? |
|----|-----------|----------------|-----------|
| H1 | Quantum and classical similarity structures differ | CKA=0.2484 | Yes |
| H2 | Quantum and classical neighborhoods differ | Jaccard k=10: 0.1004 | Yes |
| H3 | Anomaly rankings differ | Top-10 overlap: 0.2000 | Yes |
| H4 | Quantum-specific candidates exist | Count: 13 | Yes |
| H5 | Q-Interestingness is stable | Spearman: 0.7977 | Yes |
| H6 | Behavior transfers across datasets | Cross-dataset tested | Yes |

---

## 4. Dataset

- **Dataset 1**: UCI Red Wine Quality — 1,599 observations, 11 features, target: quality
- **Dataset 2**: sklearn Wine — 178 observations, 13 features, 3 classes
- **Quantum features** (4 qubits): alcohol, volatile acidity, sulphates, citric acid
- **Quantum subsample**: N=150, deterministic (seed=42)

---

## 5. Preprocessing

- No observations silently removed; duplicates documented
- Features scaled to [0, π] using MinMaxScaler for quantum encoding
- Features standardized (StandardScaler) for classical methods
- Random seed: 42 throughout all experiments

---

## 6. Classical Methodology

- Kernel: RBF (gamma=1/n_features)
- Anomaly detection: IsolationForest (contamination=0.1, seed=42)
- Supplementary: LOF (n_neighbors=20)
- Dimensionality reduction: PCA (sklearn), UMAP (umap-learn)

---

## 7. Quantum Methodology

- Feature map: ZZFeatureMap (feature_dimension=4, reps=2, entanglement=linear)
- Quantum state: |ψ(x)⟩ via Statevector simulation
- Kernel: K_ij = |⟨ψ(x_i)|ψ(x_j)⟩|²
- Implementation: FidelityQuantumKernel + ComputeUncompute + StatevectorSampler
- Note: All quantum computations are classical simulations (no quantum hardware used)

---

## 8. Q-Interestingness Definition

```
QI(x) = 0.40 * QAS(x) + 0.20 * CAS(x) + 0.20 * N(x) + 0.20 * B(x)
```

- **QAS** = 1 − mean_j≠i(K_ij)  [quantum anomaly score]
- **CAS** = IsolationForest anomaly score [classical]
- **N(x)** = 1 − mean similarity to top-5 quantum neighbors [quantum novelty]
- **B(x)** = variance of kernel row [quantum boundary, prototype metric]

All components normalized to [0,1]. Three weight configurations tested.

---

## 9. Experimental Setup

| Experiment | Configuration |
|-----------|---------------|
| Primary kernel | ZZFeatureMap, reps=2, N=150, seed=42 |
| Feature map comparison | ZZFeatureMap vs ZFeatureMap, reps=2 |
| Depth robustness | reps ∈ {1, 2, 3} |
| Permutation control | 10 permuted datasets, seeds 0–9 |
| Scalability | N ∈ {50, 100, 150, 200} |
| Second dataset | sklearn Wine, N=150 subsample |

---

## 10. Results

### Primary Metrics (Dataset 1 — Red Wine Quality, N=150)

| Metric | Value |
|--------|-------|
| Classical–Quantum CKA | **0.248383** |
| Neighborhood Jaccard k=5 | 0.1064 ± 0.1184 |
| Neighborhood Jaccard k=10 | 0.1004 ± 0.0799 |
| Neighborhood Jaccard k=15 | 0.1085 ± 0.0828 |
| Top-5 anomaly overlap | 0.0000 |
| Top-10 anomaly overlap | **0.2000** |
| Top-20 anomaly overlap | 0.2000 |
| Quantum-only candidates | **13** |
| QI rank stability (Spearman) | **0.7977** |
| Permutation z-score | **9.14** |

### Top-10 Q-Interesting Observations

| Observation | QI Score | QAS | CAS | Category |
|-------------|---------|-----|-----|----------|
| obs_415 | 1.0000 | 0.9492 | 0.7423 | Both |
| obs_506 | 0.9836 | 0.9359 | 0.7268 | Both |
| obs_1230 | 0.9818 | 1.0000 | 0.5720 | Quantum-only |
| obs_483 | 0.8852 | 0.8065 | 0.7207 | Classical-only |
| obs_1026 | 0.8587 | 0.9383 | 0.4030 | Quantum-only |
| obs_535 | 0.8440 | 0.8063 | 0.5539 | Neither |
| obs_482 | 0.8396 | 0.7750 | 0.6703 | Classical-only |
| obs_350 | 0.8323 | 0.8319 | 0.4947 | Neither |
| obs_802 | 0.8321 | 0.7259 | 0.7503 | Classical-only |
| obs_1269 | 0.8097 | 0.5941 | 0.9081 | Classical-only |

---

## 11. Robustness

### Feature Map Comparison

| Feature Map | CKA | Top-10 Overlap | Runtime (s) |
|------------|-----|----------------|------------|
| ZZFeatureMap | 0.2494 | 0.2000 | 60.0 |
| ZFeatureMap | 0.6407 | 0.3000 | 65.8 |

### Circuit Depth Robustness (ZZFeatureMap)

| reps | Depth | CKA | Top-10 Overlap | Runtime (s) |
|------|-------|-----|----------------|------------|
| 1 | 11 | 0.2853 | 0.2000 | 48.6 |
| 2 | 19 | 0.2493 | 0.2000 | 51.9 |
| 3 | 27 | 0.2210 | 0.1000 | 58.5 |

### Cross-Dataset Validation

| Dataset | N | CKA | Jaccard k=10 | Top-10 Overlap | Quantum-only |
|---------|---|-----|-------------|----------------|-------------|
| Red Wine Quality (UCI) | 150 | 0.2484 | 0.1004 | 0.2000 | 13 |
| sklearn Wine | 150 | 0.2903 | 0.1643 | 0.1000 | 13 |

---

## 12. Permutation Control

| Metric | Value |
|--------|-------|
| Permutation mean CKA (10 runs) | 0.183730 |
| Permutation std CKA | 0.007073 |
| Observed CKA | 0.248383 |
| Standardized difference (z) | **9.14** |

**Note**: z=9.14 indicates the observed CKA is 9.1 standard deviations above the
permutation null. This is NOT interpreted as a formal p-value but suggests the observed
kernel structure is not trivially explained by chance alignment.

---

## 13. Limitations

1. All quantum computations use classical statevector simulation — no quantum hardware used.
2. Quantum kernel limited to N=150 due to O(N²) computation cost.
3. ZZFeatureMap with linear entanglement is one of many possible circuit architectures.
4. Q-Interestingness weights (0.40/0.20/0.20/0.20) are heuristically chosen.
5. Quantum boundary metric B(x) is a prototype; no formal theoretical justification.
6. No claim of quantum advantage is made or implied.
7. Results may vary with different random seeds, feature selections, or circuit designs.

---

## 14. Discussion

The Q-Interestingness framework provides a structured methodology for comparing classical and
quantum exploratory data analysis. The CKA of 0.2484 (range [0,1], where 1 = identical) and
neighborhood Jaccard of 0.1004 (k=10) both indicate that quantum and classical feature
spaces identify meaningfully different structural relationships in the data.

The permutation z-score of 9.14 suggests this structural difference is not trivially
explained by noise. 13 observations were identified as quantum-specific exploratory
candidates — observations that score high in quantum anomaly space but not in classical
anomaly space. These warrant follow-up investigation.

The ZFeatureMap shows notably higher CKA (0.6407)
than ZZFeatureMap (0.2494),
suggesting that entanglement structure significantly affects kernel geometry.

---

## 15. Conclusion

**Category: A**

Strong evidence of complementary quantum exploratory structure.

Measured values (CKA=0.2484, Jaccard=0.1004, z=9.14) suggest that the
quantum feature space via ZZFeatureMap does produce a measurably different similarity structure
compared to classical RBF kernels. 13 quantum-specific exploratory candidates were
identified. Q-Interestingness rankings were stable across weight configurations (Spearman=0.7977).

These findings do NOT constitute evidence of quantum computational advantage. They represent
a preliminary characterization of complementary exploratory structure and should be validated
with broader datasets, alternative circuit designs, and — ultimately — actual quantum hardware.

---

*Generated automatically from experimental results. No values fabricated.*
*Python 3.13.14, Qiskit 2.5.2, qiskit-machine-learning 0.9.1*
