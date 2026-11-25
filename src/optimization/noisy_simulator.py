"""Noisy QAOA sampling with Qiskit Aer (not real QPU)."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from qiskit.circuit.library import QAOAAnsatz
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from src.cdc.ising import IsingHamiltonian, cost_operator_without_identity
from src.cdc.qubo import QuboModel
from src.optimization.metrics import summarize_counts, total_variation_distance
from src.optimization.qaoa import _counts_to_x_endian


def build_synthetic_noise_model(
    *,
    p1: float = 0.001,
    p2: float = 0.01,
) -> tuple[NoiseModel, dict[str, Any]]:
    """Parametric depolarizing noise — synthetic, not a device snapshot."""
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["rz", "sx", "x", "h", "rx", "ry"])
    noise.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cx", "rzz", "cz"])
    meta = {
        "type": "synthetic_depolarizing",
        "p1": p1,
        "p2": p2,
        "reference_date": None,
        "limitations": "Not derived from a real IBM backend calibration.",
    }
    return noise, meta


def try_fake_backend_noise() -> tuple[NoiseModel | None, dict[str, Any]]:
    """Attempt to load a fake backend noise model if available."""
    try:
        from qiskit_aer.noise import NoiseModel
        from qiskit.providers.fake_provider import GenericBackendV2

        backend = GenericBackendV2(num_qubits=5, seed=42)
        noise = NoiseModel.from_backend(backend)
        meta = {
            "type": "generic_backend_v2",
            "num_qubits": 5,
            "seed": 42,
            "reference_date": "runtime_generated",
            "limitations": "GenericBackendV2 approximate noise; not a live IBM device snapshot.",
        }
        return noise, meta
    except Exception as exc:  # noqa: BLE001
        return None, {"type": "unavailable", "error": str(exc)}


def sample_qaoa_with_noise(
    model: QuboModel,
    ising: IsingHamiltonian,
    parameters: list[float],
    *,
    p: int,
    shots: int = 4096,
    seed: int = 42,
    noise_mode: str = "synthetic",
    optimal_bitstrings: set[str] | None = None,
    feasible_bitstrings: set[str] | None = None,
    cost_fn=None,
    ideal_distribution: dict[str, float] | None = None,
) -> dict[str, Any]:
    circuit = QAOAAnsatz(cost_operator=cost_operator_without_identity(ising), reps=p)
    measured = circuit.assign_parameters(parameters)
    measured.measure_all()

    if noise_mode == "fake_backend":
        noise, noise_meta = try_fake_backend_noise()
        if noise is None:
            noise, noise_meta = build_synthetic_noise_model()
            noise_meta["fallback_from"] = "fake_backend"
    else:
        noise, noise_meta = build_synthetic_noise_model()

    backend = AerSimulator(noise_model=noise, seed_simulator=seed)
    t0 = time.perf_counter()
    # Transpile-free path: Aer accepts basis loosely; decompose for safety.
    job = backend.run(measured.decompose(reps=3), shots=shots)
    result = job.result()
    runtime = time.perf_counter() - t0
    raw = result.get_counts()
    counts = _counts_to_x_endian(raw, model.n_vars)
    summary = summarize_counts(
        counts,
        optimal_bitstrings=optimal_bitstrings or set(),
        feasible_bitstrings=feasible_bitstrings,
        cost_fn=cost_fn or model.evaluate,
    )
    tvd = None
    if ideal_distribution is not None:
        tvd = total_variation_distance(ideal_distribution, summary["distribution"])
    return {
        "execution_type": "noisy_simulator",
        "backend": "AerSimulator",
        "noise": noise_meta,
        "p": p,
        "shots": shots,
        "seed": seed,
        "parameters": parameters,
        "counts": counts,
        "sampling_time_seconds": runtime,
        "tvd_vs_ideal": tvd,
        **{k: v for k, v in summary.items() if k != "distribution"},
        "distribution": summary["distribution"],
        "note": "Noisy simulation is NOT execution on a real quantum computer.",
    }
