#!/usr/bin/env python3
"""Run classical baseline on the White Paper two-truck example and scenario A."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cdc.qubo import two_truck_example
from src.datasets.synthetic import generate_scenario
from src.optimization.classical import (
    enumerate_exact,
    individual_greedy,
    solve_classical_mip_like,
    uniform_random_sample,
)
from src.results_io import environment_snapshot, utc_now, write_json


def main() -> None:
    out = ROOT / "results" / "quantum_poc_v0.1"
    out.mkdir(parents=True, exist_ok=True)

    model = two_truck_example()
    exact = enumerate_exact(model)
    uniform = uniform_random_sample(
        model,
        shots=4096,
        seed=42,
        optimal_bitstrings={o["bitstring"] for o in exact["optima"]},
    )

    plans, compiled = generate_scenario("A")
    greedy = individual_greedy(compiled)
    feas = solve_classical_mip_like(compiled)

    payload = {
        "created_at_utc": utc_now(),
        "environment": environment_snapshot(ROOT),
        "two_truck_whitepaper": {
            "enumeration": {
                "optimal_cost": exact["optimal_cost"],
                "optima": exact["optima"],
                "all_solutions": exact["all_solutions"],
                "runtime_seconds": exact["runtime_seconds"],
            },
            "uniform_baseline": uniform,
            "modeling_gain_brl": 50.0,
            "modeling_gain_pct": 50.0 / 660.0 * 100.0,
            "note": "Gain is from joint modeling, NOT quantum advantage.",
        },
        "scenario_A_one_hot": {
            "greedy": greedy,
            "feasible_optimum": {
                "optimal_operational_cost": feas["optimal_operational_cost"],
                "optima": feas["optima"],
                "n_feasible": feas["n_feasible"],
            },
        },
    }
    write_json(out / "classical_results.json", payload)
    print(f"Wrote {out / 'classical_results.json'}")
    print("Two-truck optima:", exact["optima"])
    print("Scenario A operational optima:", feas["optima"])


if __name__ == "__main__":
    main()
