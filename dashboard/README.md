# Q-Interestingness: Interactive Exploration Dashboard

An interactive visualization application built with [Streamlit](https://streamlit.io/) for exploring the geometric divergence between classical Euclidean space and quantum Hilbert state space.

---

## Features

1. **Dual Representation Embedding**: Side-by-side Kernel PCA projections of classical RBF space and quantum `ZZFeatureMap` space.
2. **Interactive Threshold Filtering**: Dynamic anomaly percentile thresholding ($p \in [80, 99]$) categorizing observations into four quadrants:
   - **Quantum-only**: Typical in classical feature space, but highly isolated or heterogeneous in quantum space.
   - **Classical-only**: Identified as classical Isolation Forest outliers, but typical in quantum state fidelity.
   - **Both**: Consensus anomalies detected across both representations.
   - **Neither**: Typical bulk observations.
3. **Similarity Heatmaps**: Pairwise affinity heatmaps comparing classical Gaussian kernel vs quantum fidelity kernel.
4. **Candidate Feature Profiler**: Detailed multi-feature radar/bar profiles of individual exploratory candidates against the background population mean and variance.

---

## Launch Instructions

From the project root directory, launch the dashboard using:

```powershell
streamlit run dashboard/app.py
```

The application will open in your default browser at `http://localhost:8501`.
