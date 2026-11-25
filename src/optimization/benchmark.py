"""Hybrid classical/quantum benchmark suite for PoC sizes."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import QuboModel
from src.cdc.compiler import CompiledDecision
from src.optimization.classical import (
    enumerate_exact,
    individual_greedy,
    solve_classical_mip_like,
    uniform_random_sample,
)
from src.optimization.metrics import optimality_gap_pct
from src.optimization.noisy_simulator import sample_qaoa_with_noise
from src.optimization.qaoa import run_qaoa


def _feasible_bitstrings(compiled: CompiledDecision) -> set[str]:
    feas = solve_classical_mip_like(compiled)
    return {r["bitstring"] for r in feas["all_feasible"]}


def benchmark_instance(
    compiled: CompiledDecision,
    *,
    p: int = 2,
    shots: int = 2048,
    seed: int = 42,
    run_noisy: bool = True,
    max_qubits: int = 12,
    maxiter: int = 80,
    n_restarts: int = 2,
    run_qaoa_flag: bool = True,
    qaoa_timeout_seconds: float | None = 90.0,
) -> dict[str, Any]:
    model = compiled.qubo
    if model.n_vars > max_qubits:
        return {
            "status": "skipped",
            "reason": f"n_vars={model.n_vars} exceeds max_qubits={max_qubits}",
            "instance_id": compiled.metadata.get("instance_id"),
        }

    # Full 2^n QUBO enumeration becomes expensive; keep feasible enumeration always.
    exact = None
    if model.n_vars <= 10:
        exact = enumerate_exact(model)
    feas = solve_classical_mip_like(compiled)
    greedy = individual_greedy(compiled)
    optimal_ops = float(feas["optimal_operational_cost"])
    optimal_bitstrings = {
        r["bitstring"]
        for r in feas["optima"]
    }
    # For unconstrained toy (2-var whitepaper encoded without one-hot on single bits),
    # fall back to QUBO optima bitstrings.
    if not optimal_bitstrings and exact is not None:
        optimal_bitstrings = {r["bitstring"] for r in exact["optima"]}

    feasible_set = _feasible_bitstrings(compiled)
    uniform = uniform_random_sample(
        model, shots=shots, seed=seed, optimal_bitstrings=optimal_bitstrings
    )

    if not run_qaoa_flag:
        return {
            "status": "classical_only",
            "reason": "QAOA skipped by configuration for this instance size/budget",
            "row": {
                "instance_id": compiled.metadata.get("instance_id"),
                "number_of_variables": model.n_vars,
                "number_of_feasible_solutions": feas["n_feasible"],
                "optimal_classical_cost": optimal_ops,
                "greedy_operational_cost": greedy["operational_cost"],
                "greedy_feasible": greedy["feasible"],
                "uniform_optimal_probability": uniform["optimal_probability"],
                "qaoa_best_observed_cost": None,
                "qaoa_best_feasible_cost": None,
                "qaoa_expected_energy": None,
                "qaoa_optimal_probability": None,
                "qaoa_feasibility_rate": None,
                "qaoa_optimality_gap_pct": None,
                "shots": shots,
                "p": p,
                "seed": seed,
                "qaoa_status": "skipped",
            },
            "exact_qubo_optima": None if exact is None else exact["optima"],
            "feasible_optima": feas["optima"],
            "greedy": greedy,
            "uniform": uniform,
            "qaoa": None,
            "noisy": None,
        }

    ising = qubo_to_ising(model)

    qaoa = run_qaoa(
        model,
        ising,
        p=p,
        shots=shots,
        seed=seed,
        optimal_bitstrings=optimal_bitstrings,
        feasible_bitstrings=feasible_set,
        cost_fn=compiled.operational_cost,
        n_restarts=n_restarts,
        maxiter=maxiter,
        timeout_seconds=qaoa_timeout_seconds,
    )
    if qaoa.metadata.get("timed_out"):
        return {
            "status": "interrupted",
            "reason": f"QAOA timed out after {qaoa_timeout_seconds}s; not reported as completed",
            "row": {
                "instance_id": compiled.metadata.get("instance_id"),
                "number_of_variables": model.n_vars,
                "number_of_feasible_solutions": feas["n_feasible"],
                "optimal_classical_cost": optimal_ops,
                "greedy_operational_cost": greedy["operational_cost"],
                "qaoa_status": "interrupted_timeout",
                "qaoa_training_time_seconds": qaoa.training_time_seconds,
                "shots": shots,
                "p": p,
                "seed": seed,
            },
            "exact_qubo_optima": None if exact is None else exact["optima"],
            "feasible_optima": feas["optima"],
            "greedy": greedy,
            "uniform": uniform,
            "qaoa": qaoa.to_dict(),
            "noisy": None,
        }

    noisy = None
    if run_noisy:
        noisy = sample_qaoa_with_noise(
            model,
            ising,
            qaoa.final_parameters,
            p=p,
            shots=shots,
            seed=seed,
            optimal_bitstrings=optimal_bitstrings,
            feasible_bitstrings=feasible_set,
            cost_fn=compiled.operational_cost,
            ideal_distribution={
                k: v / qaoa.shots for k, v in qaoa.counts.items()
            },
        )

    best_feas_qaoa = None
    if qaoa.best_observed_bitstring and qaoa.best_observed_bitstring in feasible_set:
        best_feas_qaoa = compiled.operational_cost(
            [int(c) for c in qaoa.best_observed_bitstring]
        )
    else:
        # scan counted feasible
        for bs, _ in sorted(qaoa.counts.items(), key=lambda kv: -kv[1]):
            if bs in feasible_set:
                best_feas_qaoa = compiled.operational_cost([int(c) for c in bs])
                break

    row = {
        "instance_id": compiled.metadata.get("instance_id"),
        "number_of_variables": model.n_vars,
        "number_of_feasible_solutions": feas["n_feasible"],
        "optimal_classical_cost": optimal_ops,
        "greedy_operational_cost": greedy["operational_cost"],
        "greedy_feasible": greedy["feasible"],
        "uniform_optimal_probability": uniform["optimal_probability"],
        "qaoa_best_observed_cost": qaoa.best_observed_cost,
        "qaoa_best_feasible_cost": best_feas_qaoa,
        "qaoa_expected_energy": qaoa.expected_energy,
        "qaoa_optimal_probability": qaoa.optimal_probability,
        "qaoa_feasibility_rate": qaoa.feasibility_rate,
        "qaoa_optimality_gap_pct": optimality_gap_pct(best_feas_qaoa, optimal_ops),
        "qaoa_runtime_seconds": qaoa.training_time_seconds + qaoa.sampling_time_seconds,
        "qaoa_training_time_seconds": qaoa.training_time_seconds,
        "qaoa_sampling_time_seconds": qaoa.sampling_time_seconds,
        "circuit_depth": qaoa.circuit_depth,
        "two_qubit_gate_count": qaoa.two_qubit_gate_count,
        "shots": shots,
        "optimizer_evaluations": qaoa.n_evaluations,
        "p": p,
        "seed": seed,
    }
    if noisy:
        row.update(
            {
                "noisy_optimal_probability": noisy["optimal_probability"],
                "noisy_feasibility_rate": noisy["feasibility_rate"],
                "noisy_tvd_vs_ideal": noisy["tvd_vs_ideal"],
                "noisy_best_observed_cost": noisy["best_observed_cost"],
            }
        )

    row["qaoa_status"] = "completed"
    return {
        "status": "completed",
        "row": row,
        "exact_qubo_optima": None if exact is None else exact["optima"],
        "feasible_optima": feas["optima"],
        "greedy": greedy,
        "uniform": uniform,
        "qaoa": qaoa.to_dict(),
        "noisy": noisy,
    }


def rows_to_dataframe(results: list[dict[str, Any]]) -> pd.DataFrame:
    # Include classical_only rows; exclude interrupted incomplete QAOA as completed.
    rows = [
        r["row"]
        for r in results
        if r.get("status") in {"completed", "classical_only"} and "row" in r
    ]
    return pd.DataFrame(rows)
