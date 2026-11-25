"""Ideal QAOA simulation experiments."""

from __future__ import annotations

from typing import Any

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import QuboModel, two_truck_example
from src.optimization.classical import enumerate_exact, uniform_random_sample
from src.optimization.qaoa import run_qaoa


def run_ideal_qaoa_sweep(
    model: QuboModel | None = None,
    *,
    p_values: list[int] | None = None,
    seeds: list[int] | None = None,
    shots: int = 4096,
    n_restarts: int = 3,
    maxiter: int = 120,
    cost_fn=None,
    optimal_bitstrings: set[str] | None = None,
) -> dict[str, Any]:
    model = model or two_truck_example()
    p_values = p_values or [1, 2, 3]
    seeds = seeds or [42, 123, 2026]
    ising = qubo_to_ising(model)
    exact = enumerate_exact(model)
    if optimal_bitstrings is None:
        optimal_bitstrings = {r["bitstring"] for r in exact["optima"]}

    uniform = uniform_random_sample(
        model, shots=shots, seed=seeds[0], optimal_bitstrings=optimal_bitstrings
    )

    runs = []
    for p in p_values:
        for seed in seeds:
            result = run_qaoa(
                model,
                ising,
                p=p,
                shots=shots,
                seed=seed,
                maxiter=maxiter,
                n_restarts=n_restarts,
                optimal_bitstrings=optimal_bitstrings,
                cost_fn=cost_fn or model.evaluate,
            )
            runs.append(result.to_dict())

    # Select best local config by optimal probability then expected energy.
    best = max(runs, key=lambda r: (r["optimal_probability"], -r["expected_energy"]))
    return {
        "execution_type": "ideal_simulator",
        "backend": "StatevectorEstimator+StatevectorSampler",
        "model_metadata": model.metadata,
        "exact": {
            "optimal_cost": exact["optimal_cost"],
            "optima": [
                {"bitstring": o["bitstring"], "cost": o["cost"]} for o in exact["optima"]
            ],
        },
        "uniform_baseline": uniform,
        "runs": runs,
        "selected_parameters": {
            "p": best["p"],
            "seed": best["seed"],
            "parameter_names": best["parameter_names"],
            "final_parameters": best["final_parameters"],
            "optimal_probability": best["optimal_probability"],
            "expected_energy": best["expected_energy"],
        },
    }
