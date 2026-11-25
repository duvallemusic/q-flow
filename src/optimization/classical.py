"""Classical baselines for decision assignment."""

from __future__ import annotations

import time
from itertools import product
from typing import Any

import numpy as np

from src.cdc.compiler import CompiledDecision
from src.cdc.constraints import validate_one_hot
from src.cdc.qubo import QuboModel


def enumerate_exact(model: QuboModel) -> dict[str, Any]:
    t0 = time.perf_counter()
    rows = model.enumerate()
    best = min(r["cost"] for r in rows)
    optima = [r for r in rows if np.isclose(r["cost"], best)]
    return {
        "method": "exact_enumeration",
        "n_vars": model.n_vars,
        "n_states": len(rows),
        "optimal_cost": best,
        "optima": optima,
        "all_solutions": rows,
        "runtime_seconds": time.perf_counter() - t0,
    }


def individual_greedy(compiled: CompiledDecision) -> dict[str, Any]:
    """Pick cheapest plan per vehicle, ignoring cross-vehicle conflicts."""
    t0 = time.perf_counter()
    bits = [0] * compiled.qubo.n_vars
    chosen: list[dict[str, Any]] = []
    for group in compiled.groups:
        best_i = min(group, key=lambda i: compiled.plans[i].operational_cost_brl)
        bits[best_i] = 1
        chosen.append(compiled.variable_map[best_i])
    validation = compiled.validate(bits)
    return {
        "method": "individual_min_cost_ignoring_conflicts",
        "bits": bits,
        "bitstring": "".join(str(b) for b in bits),
        "operational_cost": compiled.operational_cost(bits),
        "qubo_value": compiled.qubo.evaluate(bits),
        "feasible": validation["feasible"],
        "violations": validation["violations"],
        "chosen": chosen,
        "runtime_seconds": time.perf_counter() - t0,
    }


def uniform_random_sample(
    model: QuboModel,
    *,
    shots: int,
    seed: int,
    optimal_bitstrings: set[str] | None = None,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    counts: dict[str, int] = {}
    for _ in range(shots):
        bits = rng.integers(0, 2, size=model.n_vars)
        key = "".join(str(int(b)) for b in bits)
        counts[key] = counts.get(key, 0) + 1
    opt_prob = None
    if optimal_bitstrings is not None and shots:
        opt_prob = sum(counts.get(b, 0) for b in optimal_bitstrings) / shots
    return {
        "method": "uniform_random",
        "shots": shots,
        "seed": seed,
        "counts": counts,
        "optimal_probability": opt_prob,
        "theoretical_optimal_probability": (
            len(optimal_bitstrings) / (2**model.n_vars) if optimal_bitstrings else None
        ),
        "runtime_seconds": time.perf_counter() - t0,
    }


def enumerate_feasible(compiled: CompiledDecision) -> dict[str, Any]:
    """Enumerate only one-hot-feasible assignments (Cartesian product of plans)."""
    t0 = time.perf_counter()
    group_choices = []
    for group in compiled.groups:
        options = []
        for idx in group:
            bits = [0] * compiled.qubo.n_vars
            bits[idx] = 1
            options.append((idx, bits))
        group_choices.append(options)

    rows = []
    for combo in product(*[[c[0] for c in g] for g in group_choices]):
        bits = [0] * compiled.qubo.n_vars
        for idx in combo:
            bits[idx] = 1
        assert validate_one_hot(bits, compiled.groups)["feasible"]
        op = compiled.operational_cost(bits)
        qubo_val = compiled.qubo.evaluate(bits)
        rows.append(
            {
                "bits": tuple(bits),
                "bitstring": "".join(str(b) for b in bits),
                "operational_cost": op,
                "qubo_value": qubo_val,
            }
        )
    best = min(r["operational_cost"] for r in rows)
    optima = [r for r in rows if np.isclose(r["operational_cost"], best)]
    return {
        "method": "feasible_enumeration",
        "n_feasible": len(rows),
        "optimal_operational_cost": best,
        "optima": optima,
        "all_feasible": rows,
        "runtime_seconds": time.perf_counter() - t0,
    }


def solve_classical_mip_like(compiled: CompiledDecision) -> dict[str, Any]:
    """Exact classical optimum over feasible assignments (enumerative MIP-equivalent for PoC sizes).

    For the PoC qubit budget (<=12), feasible enumeration is exact and transparent.
    OR-Tools is optional; this method documents that brute force over ALL 2^n states
    is NOT the only classical baseline — feasible enumeration / assignment search is used.
    """
    result = enumerate_feasible(compiled)
    result["method"] = "classical_feasible_optimum"
    result["note"] = (
        "Exact optimum over one-hot feasible assignments via Cartesian enumeration; "
        "suitable for PoC sizes. Not claimed as industrial MIP performance."
    )
    return result
