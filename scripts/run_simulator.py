#!/usr/bin/env python3
"""Ideal QAOA sweep on the White Paper two-truck instance."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import two_truck_example
from src.optimization.simulator import run_ideal_qaoa_sweep
from src.results_io import environment_snapshot, utc_now, write_json


def main() -> None:
    out = ROOT / "results" / "quantum_poc_v0.1"
    charts = out / "charts"
    charts.mkdir(parents=True, exist_ok=True)

    model = two_truck_example()
    result = run_ideal_qaoa_sweep(model, p_values=[1, 2, 3], seeds=[42, 123, 2026], shots=4096)
    payload = {
        "created_at_utc": utc_now(),
        "environment": environment_snapshot(ROOT),
        **result,
    }
    write_json(out / "simulator_results.json", payload)
    write_json(out / "optimized_parameters.json", result["selected_parameters"])
    write_json(
        out / "ising_hamiltonians.json",
        {
            "two_truck": {
                "paulis": [
                    {"label": lab, "coeff_real": float(c.real)}
                    for lab, c in zip(
                        qubo_to_ising(model).operator.paulis.to_labels(),
                        qubo_to_ising(model).operator.coeffs,
                        strict=True,
                    )
                ],
                "expected": {
                    "I": 627.5,
                    "Z1": 7.5,
                    "Z2": 7.5,
                    "Z1Z2": 17.5,
                },
            }
        },
    )
    write_json(
        out / "qubo_instances.json",
        {
            "two_truck": {
                "linear": model.linear,
                "quadratic": {f"{i},{j}": v for (i, j), v in model.quadratic.items()},
                "offset": model.offset,
                "metadata": model.metadata,
            }
        },
    )

    # Convergence chart for selected run
    selected = result["selected_parameters"]
    selected_run = next(
        r
        for r in result["runs"]
        if r["p"] == selected["p"] and r["seed"] == selected["seed"]
    )
    hist_path = out / "convergence_history.csv"
    with hist_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["evaluation", "energy"])
        for i, val in enumerate(selected_run["objective_history"]):
            writer.writerow([i, val])

    plt.figure(figsize=(7, 4))
    plt.plot(selected_run["objective_history"], color="#1f4e79")
    plt.xlabel("Evaluation")
    plt.ylabel("⟨H⟩")
    plt.title(f"QAOA convergence (p={selected['p']}, seed={selected['seed']})")
    plt.tight_layout()
    plt.savefig(charts / "qaoa_convergence.png", dpi=150)
    plt.close()

    # Ideal distribution
    counts = selected_run["counts"]
    labels = sorted(counts)
    values = [counts[k] / selected_run["shots"] for k in labels]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color="#2a9d8f")
    plt.xlabel("Bitstring (x1 x2)")
    plt.ylabel("Probability")
    plt.title("Ideal QAOA distribution (synthetic two-truck)")
    plt.tight_layout()
    plt.savefig(charts / "ideal_distribution.png", dpi=150)
    plt.close()

    # Optimal probability across p
    by_p = {}
    for r in result["runs"]:
        by_p.setdefault(r["p"], []).append(r["optimal_probability"])
    ps = sorted(by_p)
    means = [sum(by_p[p]) / len(by_p[p]) for p in ps]
    plt.figure(figsize=(6, 4))
    plt.plot(ps, means, marker="o", color="#e76f51")
    plt.axhline(0.5, color="gray", linestyle="--", label="Uniform baseline (50%)")
    plt.xlabel("p")
    plt.ylabel("Mean P(optimal)")
    plt.legend()
    plt.title("Optimal probability vs p")
    plt.tight_layout()
    plt.savefig(charts / "optimal_probability.png", dpi=150)
    plt.close()

    print("Selected parameters:", result["selected_parameters"])
    print(f"Wrote results under {out}")


if __name__ == "__main__":
    main()
