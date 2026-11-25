#!/usr/bin/env python3
"""Scalability benchmark across synthetic scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import two_truck_example
from src.datasets.synthetic import generate_scenario, list_scenarios
from src.optimization.benchmark import benchmark_instance, rows_to_dataframe
from src.optimization.qaoa import run_qaoa
from src.results_io import environment_snapshot, utc_now, write_json


def main() -> None:
    out = ROOT / "results" / "quantum_poc_v0.1"
    charts = out / "charts"
    charts.mkdir(parents=True, exist_ok=True)

    results = []
    # Scenario D (12 binary vars) previously hung local QAOA for >10 min on M4 16GB.
    # Policy: classical-only for D; QAOA only up to scenario C with hard timeout.
    configs = {
        "A": {
            "shots": 1024,
            "p": 1,
            "noisy": False,
            "maxiter": 40,
            "restarts": 1,
            "run_qaoa": True,
            "timeout": 60.0,
        },
        "B": {
            "shots": 512,
            "p": 1,
            "noisy": False,
            "maxiter": 25,
            "restarts": 1,
            "run_qaoa": True,
            "timeout": 60.0,
        },
        "C": {
            "shots": 256,
            "p": 1,
            "noisy": False,
            "maxiter": 15,
            "restarts": 1,
            "run_qaoa": True,
            "timeout": 45.0,
        },
        "D": {
            "shots": 256,
            "p": 1,
            "noisy": False,
            "maxiter": 5,
            "restarts": 1,
            "run_qaoa": False,
            "timeout": 30.0,
        },
    }
    for name, cfg in configs.items():
        _, compiled = generate_scenario(name)
        print(f"Benchmarking scenario {name} (n={compiled.qubo.n_vars})...", flush=True)
        result = benchmark_instance(
            compiled,
            p=cfg["p"],
            shots=cfg["shots"],
            seed=42,
            run_noisy=cfg["noisy"],
            max_qubits=12,
            maxiter=cfg["maxiter"],
            n_restarts=cfg["restarts"],
            run_qaoa_flag=cfg["run_qaoa"],
            qaoa_timeout_seconds=cfg["timeout"],
        )
        results.append(result)
        print(
            " status:",
            result.get("status"),
            result.get("reason"),
            result.get("row", {}).get("qaoa_optimal_probability"),
            flush=True,
        )

    # Dedicated 2-qubit whitepaper benchmark entry (canonical encoding)
    model = two_truck_example()
    ising = qubo_to_ising(model)
    print("Benchmarking two_truck_whitepaper_2q...", flush=True)
    q = run_qaoa(
        model,
        ising,
        p=2,
        shots=4096,
        seed=42,
        optimal_bitstrings=set(model.metadata["optimal_bitstrings"]),
        n_restarts=2,
        maxiter=80,
        timeout_seconds=120.0,
    )
    results.append(
        {
            "status": "completed",
            "row": {
                "instance_id": "two_truck_whitepaper_2q",
                "number_of_variables": 2,
                "number_of_feasible_solutions": 4,
                "optimal_classical_cost": 610.0,
                "qaoa_optimal_probability": q.optimal_probability,
                "qaoa_best_feasible_cost": q.best_observed_cost,
                "qaoa_expected_energy": q.expected_energy,
                "circuit_depth": q.circuit_depth,
                "shots": 4096,
                "p": 2,
                "seed": 42,
                "qaoa_status": "completed" if not q.metadata.get("timed_out") else "interrupted_timeout",
            },
            "qaoa": q.to_dict(),
        }
    )

    df = rows_to_dataframe(results)
    df.to_csv(out / "benchmark.csv", index=False)
    write_json(
        out / "benchmark_results.json",
        {
            "created_at_utc": utc_now(),
            "environment": environment_snapshot(ROOT),
            "scenarios_available": list_scenarios(),
            "results": results,
            "notes": [
                "Scenario D QAOA skipped after hang on M4 16GB (12 qubits / one-hot encoding).",
                "Scenario E omitted by default on 16GB laptop budget.",
                "Interrupted runs are never labeled completed.",
                "Classical baseline uses feasible enumeration, not only 2^n brute force.",
            ],
            "known_failures": [
                {
                    "id": "D_qaoa_hang",
                    "scenario": "D",
                    "n_vars": 12,
                    "symptom": "Local QAOA with StatevectorEstimator did not finish within >10 minutes",
                    "action": "Marked classical_only; QAOA skipped intentionally",
                }
            ],
        },
    )

    if not df.empty and "number_of_variables" in df.columns:
        plot_df = df.dropna(subset=["qaoa_optimal_probability"])
        if not plot_df.empty:
            plt.figure(figsize=(7, 4))
            plt.plot(
                plot_df["number_of_variables"],
                plot_df["qaoa_optimal_probability"],
                marker="o",
            )
            plt.xlabel("Number of binary variables")
            plt.ylabel("QAOA P(optimal)")
            plt.title("Scaling of optimal probability (synthetic)")
            plt.tight_layout()
            plt.savefig(charts / "scaling.png", dpi=150)
            plt.close()

        if "circuit_depth" in df.columns:
            depth_df = df.dropna(subset=["circuit_depth"])
            if not depth_df.empty:
                plt.figure(figsize=(7, 4))
                plt.plot(
                    depth_df["number_of_variables"],
                    depth_df["circuit_depth"],
                    marker="s",
                    color="#264653",
                )
                plt.xlabel("Number of binary variables")
                plt.ylabel("Circuit depth")
                plt.title("QAOA circuit depth vs size")
                plt.tight_layout()
                plt.savefig(charts / "circuit_depth.png", dpi=150)
                plt.close()

        if "greedy_operational_cost" in df.columns and "optimal_classical_cost" in df.columns:
            sub = df.dropna(subset=["greedy_operational_cost"])
            if not sub.empty:
                plt.figure(figsize=(7, 4))
                x = range(len(sub))
                plt.bar(
                    [i - 0.2 for i in x],
                    sub["greedy_operational_cost"],
                    width=0.4,
                    label="Greedy",
                )
                plt.bar(
                    [i + 0.2 for i in x],
                    sub["optimal_classical_cost"],
                    width=0.4,
                    label="Optimal",
                )
                plt.xticks(list(x), sub["instance_id"], rotation=30, ha="right")
                plt.ylabel("Operational cost (BRL, synthetic)")
                plt.title("Classical greedy vs joint optimum")
                plt.legend()
                plt.tight_layout()
                plt.savefig(charts / "classical_vs_quantum.png", dpi=150)
                plt.close()

        if "qaoa_feasibility_rate" in df.columns:
            feas_df = df.dropna(subset=["qaoa_feasibility_rate"])
            if not feas_df.empty:
                plt.figure(figsize=(7, 4))
                plt.plot(
                    feas_df["number_of_variables"],
                    feas_df["qaoa_feasibility_rate"],
                    marker="o",
                    color="#9b2226",
                )
                plt.xlabel("Variables")
                plt.ylabel("Feasibility rate")
                plt.title("QAOA feasibility rate")
                plt.tight_layout()
                plt.savefig(charts / "feasibility_rate.png", dpi=150)
                plt.close()

    print(df.to_string(index=False) if not df.empty else "No completed rows")


if __name__ == "__main__":
    main()
