"""Shared metrics for classical/quantum experiment reporting."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1.0 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, center - margin), min(1.0, center + margin))


def total_variation_distance(p: dict[str, float], q: dict[str, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def optimality_gap_pct(best_feasible: float | None, optimal: float | None) -> float | None:
    if best_feasible is None or optimal is None:
        return None
    if np.isclose(optimal, 0.0):
        return abs(best_feasible - optimal)
    return (best_feasible - optimal) / abs(optimal) * 100.0


def distribution_from_counts(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in counts.items()}


def summarize_counts(
    counts: dict[str, int],
    *,
    optimal_bitstrings: set[str],
    feasible_bitstrings: set[str] | None = None,
    cost_fn=None,
) -> dict[str, Any]:
    total = sum(counts.values())
    dist = distribution_from_counts(counts)
    opt_shots = sum(counts.get(b, 0) for b in optimal_bitstrings)
    opt_prob = opt_shots / total if total else 0.0
    lo, hi = wilson_interval(opt_shots, total) if total else (float("nan"), float("nan"))
    feas_prob = None
    if feasible_bitstrings is not None and total:
        feas_shots = sum(counts.get(b, 0) for b in feasible_bitstrings)
        feas_prob = feas_shots / total
    most_frequent = max(counts, key=counts.get) if counts else None
    best_cost = None
    best_bits = None
    if cost_fn is not None and counts:
        for bitstring, _ in sorted(counts.items(), key=lambda kv: -kv[1]):
            bits = [int(c) for c in bitstring]
            c = float(cost_fn(bits))
            if best_cost is None or c < best_cost:
                best_cost = c
                best_bits = bitstring
    expected = None
    if cost_fn is not None and dist:
        expected = sum(prob * float(cost_fn([int(c) for c in bs])) for bs, prob in dist.items())
    return {
        "shots": total,
        "most_frequent": most_frequent,
        "optimal_probability": opt_prob,
        "optimal_probability_wilson_95": [lo, hi],
        "feasibility_rate": feas_prob,
        "best_observed_bitstring": best_bits,
        "best_observed_cost": best_cost,
        "expected_cost": expected,
        "distribution": dist,
    }
