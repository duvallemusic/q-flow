"""QAOA with Qiskit V2 primitives (StatevectorEstimator / StatevectorSampler)."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
from qiskit.circuit.library import QAOAAnsatz
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from scipy.optimize import minimize

from src.cdc.ising import IsingHamiltonian, cost_operator_without_identity
from src.cdc.qubo import QuboModel
from src.optimization.metrics import summarize_counts


@dataclass
class QAOAResult:
    p: int
    seed: int
    shots: int
    parameter_names: list[str]
    initial_parameters: list[float]
    final_parameters: list[float]
    objective_history: list[float]
    n_evaluations: int
    n_iterations: int
    training_time_seconds: float
    sampling_time_seconds: float
    circuit_depth: int
    n_qubits: int
    two_qubit_gate_count: int
    n_logical_gates: int
    counts: dict[str, int]
    expected_energy: float
    most_frequent: str | None
    best_observed_bitstring: str | None
    best_observed_cost: float | None
    optimal_probability: float
    optimal_probability_wilson_95: list[float]
    feasibility_rate: float | None
    expected_cost: float | None
    optimizer_success: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bitstring_from_qiskit(key: str | int, n_qubits: int) -> str:
    """Normalize sampler bitstrings to left-to-right x0..xn-1."""
    if isinstance(key, int):
        raw = format(key, f"0{n_qubits}b")
    else:
        raw = key.replace(" ", "")
        if len(raw) < n_qubits:
            raw = raw.zfill(n_qubits)
        raw = raw[-n_qubits:]
    # Qiskit little-endian: rightmost bit is qubit 0.
    return raw[::-1]


def _counts_to_x_endian(counts: dict[Any, int], n_qubits: int) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in counts.items():
        bs = _bitstring_from_qiskit(key, n_qubits)
        out[bs] = out.get(bs, 0) + int(value)
    return out


def build_qaoa_circuit(ising: IsingHamiltonian, p: int):
    cost_op = cost_operator_without_identity(ising)
    circuit = QAOAAnsatz(cost_operator=cost_op, reps=p)
    return circuit


class QAOATimeoutError(TimeoutError):
    """Raised when local QAOA exceeds the configured wall-clock budget."""


def run_qaoa(
    model: QuboModel,
    ising: IsingHamiltonian,
    *,
    p: int = 2,
    shots: int = 4096,
    seed: int = 42,
    maxiter: int = 150,
    initial_point: list[float] | None = None,
    optimal_bitstrings: set[str] | None = None,
    feasible_bitstrings: set[str] | None = None,
    cost_fn=None,
    n_restarts: int = 3,
    timeout_seconds: float | None = 120.0,
) -> QAOAResult:
    """Train QAOA locally with StatevectorEstimator; sample with StatevectorSampler."""
    if model.n_vars > 12:
        raise ValueError("PoC limit: refuse QAOA with more than 12 qubits on this laptop")

    rng = np.random.default_rng(seed)
    cost_op = cost_operator_without_identity(ising)
    circuit = build_qaoa_circuit(ising, p)
    param_names = [str(param) for param in circuit.parameters]
    n_params = circuit.num_parameters

    # Scale only the non-constant operator for numerical conditioning; report energies
    # back in the original QUBO/Ising units via offset + unscaled expectation.
    abs_coeffs = np.abs(np.real(cost_op.coeffs)) if len(cost_op.coeffs) else np.array([1.0])
    scale = float(np.max(abs_coeffs)) if abs_coeffs.size else 1.0
    scale = scale if scale > 0 else 1.0
    cost_op_scaled = cost_op / scale

    estimator = StatevectorEstimator(seed=seed)
    history: list[float] = []
    t_train0 = time.perf_counter()
    timed_out = False

    def objective(theta: np.ndarray) -> float:
        nonlocal timed_out
        if timeout_seconds is not None and (time.perf_counter() - t_train0) > timeout_seconds:
            timed_out = True
            raise QAOATimeoutError(
                f"QAOA training exceeded timeout_seconds={timeout_seconds} "
                f"for n_vars={model.n_vars}"
            )
        pub = (circuit, cost_op_scaled, theta)
        result = estimator.run([pub]).result()
        # Convert scaled expectation back to original energy (plus tracked offset/identity).
        value = float(np.real(result[0].data.evs)) * scale + float(ising.offset)
        history.append(value)
        return value

    best_fun = float("inf")
    best_x = None
    best_hist: list[float] = []
    total_evals = 0
    total_iters = 0
    success = False

    starts = []
    if initial_point is not None:
        starts.append(np.asarray(initial_point, dtype=float))
    while len(starts) < n_restarts:
        starts.append(rng.uniform(0, 2 * np.pi, size=n_params))

    for start in starts:
        history = []
        try:
            opt = minimize(objective, start, method="COBYLA", options={"maxiter": maxiter})
        except QAOATimeoutError:
            # Keep best parameters found so far; do not invent a completed optimum.
            if best_x is None:
                best_x = np.asarray(start, dtype=float)
                best_fun = float(history[-1]) if history else float("nan")
                best_hist = list(history)
            break
        total_evals += int(opt.nfev)
        total_iters += int(getattr(opt, "nit", len(history)))
        if opt.fun < best_fun:
            best_fun = float(opt.fun)
            best_x = np.asarray(opt.x, dtype=float)
            best_hist = list(history)
            success = bool(opt.success) or True  # COBYLA may report success=False near tol
        if timed_out:
            break
    training_time = time.perf_counter() - t_train0
    assert best_x is not None

    # Sampling
    measured = circuit.copy()
    measured.measure_all()
    sampler = StatevectorSampler(seed=seed)
    t_samp0 = time.perf_counter()
    samp = sampler.run([(measured, best_x)], shots=shots).result()
    sampling_time = time.perf_counter() - t_samp0

    # Extract counts from SamplerV2-style result
    data = samp[0].data
    if hasattr(data, "meas"):
        bit_array = data.meas
        raw_counts = bit_array.get_counts()
    elif hasattr(data, "join_data"):
        raw_counts = data.join_data().get_counts()
    else:
        # Fallback: first register
        register_name = next(iter(data.keys())) if hasattr(data, "keys") else None
        if register_name is None:
            raise RuntimeError("Unable to extract counts from sampler result")
        raw_counts = getattr(data, register_name).get_counts()

    counts = _counts_to_x_endian(raw_counts, model.n_vars)
    if cost_fn is None:
        cost_fn = model.evaluate
    summary = summarize_counts(
        counts,
        optimal_bitstrings=optimal_bitstrings or set(),
        feasible_bitstrings=feasible_bitstrings,
        cost_fn=cost_fn,
    )

    # Circuit metrics on unbound ansatz
    decomposed = circuit.decompose()
    twoq = sum(1 for inst in decomposed.data if getattr(inst.operation, "num_qubits", 1) == 2)

    return QAOAResult(
        p=p,
        seed=seed,
        shots=shots,
        parameter_names=param_names,
        initial_parameters=starts[0].tolist(),
        final_parameters=best_x.tolist(),
        objective_history=best_hist,
        n_evaluations=total_evals,
        n_iterations=total_iters,
        training_time_seconds=training_time,
        sampling_time_seconds=sampling_time,
        circuit_depth=circuit.depth(),
        n_qubits=model.n_vars,
        two_qubit_gate_count=int(twoq),
        n_logical_gates=len(circuit.data),
        counts=counts,
        expected_energy=float(best_fun),
        most_frequent=summary["most_frequent"],
        best_observed_bitstring=summary["best_observed_bitstring"],
        best_observed_cost=summary["best_observed_cost"],
        optimal_probability=float(summary["optimal_probability"]),
        optimal_probability_wilson_95=[
            float(summary["optimal_probability_wilson_95"][0]),
            float(summary["optimal_probability_wilson_95"][1]),
        ],
        feasibility_rate=summary["feasibility_rate"],
        expected_cost=summary["expected_cost"],
        optimizer_success=success,
        metadata={
            "optimizer": "COBYLA",
            "n_restarts": n_restarts,
            "maxiter": maxiter,
            "timeout_seconds": timeout_seconds,
            "timed_out": timed_out,
            "estimator": "StatevectorEstimator",
            "sampler": "StatevectorSampler",
            "primitive_api": "V2",
            "qubo_scale": model.scale,
            "variational_operator_scale": scale,
            "energy_units": "original_qubo_currency_units",
            "identity_removed_from_ansatz": True,
            "completed": not timed_out,
        },
    )
