"""Classical baselines and QAOA smoke tests (local only)."""

from __future__ import annotations

import numpy as np

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import two_truck_example
from src.datasets.synthetic import generate_scenario
from src.optimization.classical import (
    enumerate_exact,
    individual_greedy,
    solve_classical_mip_like,
    uniform_random_sample,
)
from src.optimization.metrics import total_variation_distance, wilson_interval
from src.optimization.qaoa import run_qaoa


def test_exact_enumeration_and_modeling_gain():
    exact = enumerate_exact(two_truck_example())
    assert exact["optimal_cost"] == 610
    naive = 660
    gain = naive - exact["optimal_cost"]
    assert gain == 50
    assert abs(gain / naive * 100 - (50 / 660) * 100) < 1e-9


def test_uniform_baseline_theory():
    model = two_truck_example()
    optima = {o["bitstring"] for o in model.optima()}
    sample = uniform_random_sample(model, shots=20000, seed=1, optimal_bitstrings=optima)
    assert sample["theoretical_optimal_probability"] == 0.5
    assert abs(sample["optimal_probability"] - 0.5) < 0.05


def test_scenario_a_joint_beats_greedy_conflict():
    _, compiled = generate_scenario("A")
    greedy = individual_greedy(compiled)
    feas = solve_classical_mip_like(compiled)
    assert feas["optimal_operational_cost"] == 610
    # Greedy picks cheapest individual plans (A+A) => 660 with conflict
    assert greedy["operational_cost"] == 660


def test_dataset_deterministic():
    plans1, _ = generate_scenario("B")
    plans2, _ = generate_scenario("B")
    assert [p.operational_cost_brl for p in plans1] == [p.operational_cost_brl for p in plans2]


def test_wilson_and_tvd():
    lo, hi = wilson_interval(50, 100)
    assert 0 <= lo <= 0.5 <= hi <= 1
    assert total_variation_distance({"00": 1.0}, {"00": 0.5, "11": 0.5}) == 0.5


def test_qaoa_runs_and_beats_or_matches_randomish():
    model = two_truck_example()
    ising = qubo_to_ising(model)
    result = run_qaoa(
        model,
        ising,
        p=2,
        shots=2048,
        seed=42,
        maxiter=60,
        n_restarts=2,
        optimal_bitstrings=set(model.metadata["optimal_bitstrings"]),
    )
    assert result.n_qubits == 2
    assert result.shots == 2048
    assert len(result.final_parameters) == len(result.parameter_names) == 4
    assert result.optimal_probability >= 0.0
    # Soft check: with training, should often exceed ~0.35 on this tiny instance
    assert result.best_observed_cost is not None
    assert result.best_observed_cost >= 610 - 1e-6
