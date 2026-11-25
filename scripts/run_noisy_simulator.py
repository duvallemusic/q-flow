#!/usr/bin/env python3
"""Noisy Aer simulation using parameters from the ideal QAOA run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import two_truck_example
from src.optimization.noisy_simulator import sample_qaoa_with_noise
from src.results_io import environment_snapshot, utc_now, write_json


def main() -> None:
    out = ROOT / "results" / "quantum_poc_v0.1"
    charts = out / "charts"
    charts.mkdir(parents=True, exist_ok=True)

    params_path = out / "optimized_parameters.json"
    sim_path = out / "simulator_results.json"
    if not params_path.exists():
        raise SystemExit("Run scripts/run_simulator.py first to produce optimized_parameters.json")

    params = json.loads(params_path.read_text(encoding="utf-8"))
    sim = json.loads(sim_path.read_text(encoding="utf-8")) if sim_path.exists() else {}
    selected_run = None
    for r in sim.get("runs", []):
        if r["p"] == params["p"] and r["seed"] == params["seed"]:
            selected_run = r
            break
    ideal_dist = None
    if selected_run:
        ideal_dist = {
            k: v / selected_run["shots"] for k, v in selected_run["counts"].items()
        }

    model = two_truck_example()
    ising = qubo_to_ising(model)
    optima = set(model.metadata["optimal_bitstrings"])

    synthetic = sample_qaoa_with_noise(
        model,
        ising,
        params["final_parameters"],
        p=params["p"],
        shots=4096,
        seed=params["seed"],
        noise_mode="synthetic",
        optimal_bitstrings=optima,
        ideal_distribution=ideal_dist,
    )
    fake = sample_qaoa_with_noise(
        model,
        ising,
        params["final_parameters"],
        p=params["p"],
        shots=4096,
        seed=params["seed"],
        noise_mode="fake_backend",
        optimal_bitstrings=optima,
        ideal_distribution=ideal_dist,
    )

    payload = {
        "created_at_utc": utc_now(),
        "environment": environment_snapshot(ROOT),
        "parameters_source": params,
        "synthetic_noise": synthetic,
        "fake_backend_noise": fake,
        "disclaimer": "Noisy simulation ≠ real QPU execution.",
    }
    write_json(out / "noisy_simulator_results.json", payload)

    labels = sorted(set(synthetic["distribution"]) | set(ideal_dist or {}))
    plt.figure(figsize=(7, 4))
    x = range(len(labels))
    ideal_vals = [(ideal_dist or {}).get(k, 0.0) for k in labels]
    noisy_vals = [synthetic["distribution"].get(k, 0.0) for k in labels]
    width = 0.35
    plt.bar([i - width / 2 for i in x], ideal_vals, width=width, label="Ideal", color="#2a9d8f")
    plt.bar([i + width / 2 for i in x], noisy_vals, width=width, label="Noisy", color="#e9c46a")
    plt.xticks(list(x), labels)
    plt.ylabel("Probability")
    plt.title("Ideal vs synthetic noisy distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(charts / "noisy_distribution.png", dpi=150)
    plt.close()

    print("Synthetic TVD vs ideal:", synthetic["tvd_vs_ideal"])
    print("Fake-backend TVD vs ideal:", fake["tvd_vs_ideal"])


if __name__ == "__main__":
    main()
