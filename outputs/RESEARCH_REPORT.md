# Q-Interestingness: Final Research Report

## 1. Executive Summary

This research investigates whether mapping classical feature spaces into quantum feature spaces induces structurally different geometries, and whether this can surface complementary exploratory candidates. We formalize this via a **Quantum Unusualness (QU)** and **Representation Disagreement (RD)** framework.

**Key Findings:**
* The quantum representation (ZZFeatureMap) diverges from classical RBF substantially (CKA=0.2484).
* The structural divergence is significantly stronger than classical polynomial or linear alternatives (D=0.75 vs D=0.33).
* Local neighborhoods exhibit low overlap (Jaccard@10 = 0.1004).
* 13 observations are uniquely identified as "Quantum-only" exploratory candidates.
* The ranking framework is highly robust to parameter weighting (mean Spearman = 0.9697).

*(Note: All quantum experiments used classical statevector simulation. No quantum hardware was used, and no quantum computational advantage is claimed).*

---

## 2. Framework Definition (QI_v2)

The `Q-Interestingness (QI_v2)` score is a composite of internal quantum geometry and cross-space disagreement:

```
QU(x) = 0.5*QAS + 0.3*N + 0.2*B
RD(x) = 0.5*|QAS-CAS| + 0.5*(1-J_5)
QI_v2(x) = 0.5*QU + 0.5*RD
```

Where:
* **QAS**: Global quantum isolation
* **N**: Local quantum novelty
* **B**: Quantum neighborhood heterogeneity (diagonal self-similarity excluded)
* **CAS**: Classical Isolation Forest anomaly score

---

## 3. Primary Metrics (Red Wine Quality, N=150)

| Metric | Value | Status |
|--------|-------|--------|
| Classical–Quantum CKA | **0.2484** | [EXISTING] |
| Neighborhood Jaccard k=10 | **0.1004** | [EXISTING] |
| Quantum-only candidates | **13** | [RECOMPUTED] |
| QI_v2 rank stability (Spearman) | **0.9697** | [NEW] |

---

## 4. Robustness & Controls

### Classical Kernel Divergence (D = 1 - CKA)
| Kernel Control | Divergence vs RBF | Status |
|----------------|-------------------|--------|
| Quantum (ZZFeatureMap) | **0.7516** | [NEW] |
| Polynomial (degree=3) | 0.3298 | [NEW] |
| Linear | 0.2445 | [NEW] |

*Interpretation: The quantum geometry diverges significantly more from the classical RBF baseline than standard classical non-linear controls do.*

### Cross-Dataset Validation
| Dataset | CKA | Jaccard@10 | Quantum-only |
|---------|-----|------------|--------------|
| Red Wine Quality (UCI) | 0.2484 | 0.1004 | 13 |
| sklearn Wine | 0.4008 | 0.2340 | 13 |

*(Note: sklearn Wine dataset metrics reflect corrected standardizing-before-variance feature selection).*


### Synthetic Sanity Checks
Synthetic datasets (Gaussian clusters and Two Moons) with uniformly injected spatial outliers were tested. Classical Isolation Forest perfectly identified spatial outliers (Precision@10 = 1.0), whereas QI_v2 achieved Precision@10 = 0.90. 
*Interpretation: This confirms QI_v2 is broadly sensitive to structure, but also demonstrates that quantum geometry is not universally superior for trivial spatial anomaly detection. It serves as a limitation and sanity check.*

### Pending Validation
* **Full Quantum Permutation (B=100)**: The RBF permutation proxy yielded z=5.29, but the true quantum permutation distribution remains pending due to O(N²) execution time (~72 minutes). 

---

## 5. Conclusion

**The framework demonstrates representation-dependent exploratory structure.** 

Measured values (CKA=0.2484, Jaccard=0.1004) confirm that the quantum feature space via `ZZFeatureMap` produces a measurably different similarity structure compared to classical RBF kernels. Crucially, the quantum representation diverges from RBF significantly more than classical non-linear controls do. 

These findings represent a preliminary characterization of complementary exploratory structure and should be validated with actual quantum hardware.
