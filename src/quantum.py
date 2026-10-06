"""
src/quantum.py — Quantum feature map and kernel construction using
current Qiskit 2.5.2 / qiskit-machine-learning 0.9.1 APIs.

API used:
  - ZZFeatureMap / ZFeatureMap  from qiskit.circuit.library (class-based)
  - StatevectorSampler           from qiskit.primitives
  - ComputeUncompute             from qiskit_machine_learning.state_fidelities
  - FidelityQuantumKernel        from qiskit_machine_learning.kernels
"""

import time
import numpy as np


def build_zz_feature_map(n_qubits: int = 4, reps: int = 2, entanglement: str = "linear"):
    """Return a ZZFeatureMap circuit (class-based API)."""
    from qiskit.circuit.library import ZZFeatureMap
    fm = ZZFeatureMap(feature_dimension=n_qubits, reps=reps, entanglement=entanglement)
    print(f"ZZFeatureMap: {n_qubits} qubits, reps={reps}, entanglement={entanglement}")
    print(f"  Circuit depth: {fm.decompose().depth()}, Parameters: {fm.num_parameters}")
    return fm


def build_z_feature_map(n_qubits: int = 4, reps: int = 2):
    """Return a ZFeatureMap circuit (class-based API)."""
    from qiskit.circuit.library import ZFeatureMap
    fm = ZFeatureMap(feature_dimension=n_qubits, reps=reps)
    print(f"ZFeatureMap: {n_qubits} qubits, reps={reps}")
    print(f"  Circuit depth: {fm.decompose().depth()}, Parameters: {fm.num_parameters}")
    return fm


def build_quantum_kernel(feature_map):
    """
    Build FidelityQuantumKernel using:
      StatevectorSampler → ComputeUncompute → FidelityQuantumKernel
    """
    from qiskit.primitives import StatevectorSampler
    from qiskit_machine_learning.state_fidelities import ComputeUncompute
    from qiskit_machine_learning.kernels import FidelityQuantumKernel

    sampler = StatevectorSampler()
    fidelity = ComputeUncompute(sampler=sampler)
    kernel = FidelityQuantumKernel(fidelity=fidelity, feature_map=feature_map)
    print("FidelityQuantumKernel built (StatevectorSampler + ComputeUncompute).")
    return kernel


def compute_kernel_matrix(kernel, X: np.ndarray) -> tuple:
    """
    Evaluate the full NxN kernel matrix.
    Returns (K, elapsed_seconds).
    """
    n = len(X)
    print(f"Computing quantum kernel matrix ({n}x{n}) ...")
    t0 = time.time()
    K = kernel.evaluate(x_vec=X)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s. K.shape={K.shape}")
    return K.astype(np.float64), elapsed


def compute_statevector_demo(feature_map, x: np.ndarray) -> np.ndarray:
    """
    Bind a single data point to the feature map and run a statevector simulation.
    Returns the full statevector amplitude array.
    """
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import Statevector

    bound = feature_map.assign_parameters(x)
    sv = Statevector(bound)
    return sv.data  # complex amplitudes


def get_measurement_probabilities(feature_map, x: np.ndarray) -> dict:
    """
    Bind a data point and return the measurement probability distribution.
    """
    from qiskit.quantum_info import Statevector
    bound = feature_map.assign_parameters(x)
    sv = Statevector(bound)
    probs = sv.probabilities_dict()
    return probs
