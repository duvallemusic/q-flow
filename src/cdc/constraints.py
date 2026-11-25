"""Constraint helpers for one-hot vehicle/plan encodings."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def one_hot_penalty(
    groups: list[list[int]],
    *,
    penalty: float,
) -> tuple[dict[int, float], dict[tuple[int, int], float], float]:
    """Expand λ Σ_g (Σ_{k in g} x_k - 1)^2 into linear/quadratic/offset terms.

    (Σ x_k - 1)^2 = Σ x_k^2 + 2 Σ_{i<j} x_i x_j - 2 Σ x_k + 1
                  = Σ x_k + 2 Σ_{i<j} x_i x_j - 2 Σ x_k + 1   (since x^2=x)
                  = -Σ x_k + 2 Σ_{i<j} x_i x_j + 1
    """
    linear: dict[int, float] = defaultdict(float)
    quadratic: dict[tuple[int, int], float] = defaultdict(float)
    offset = 0.0
    for group in groups:
        offset += float(penalty) * 1.0
        for i in group:
            linear[i] += -float(penalty)
        for a_idx, i in enumerate(group):
            for j in group[a_idx + 1 :]:
                a, b = (i, j) if i < j else (j, i)
                quadratic[(a, b)] += 2.0 * float(penalty)
    return dict(linear), dict(quadratic), offset


def validate_one_hot(
    bits: list[int] | tuple[int, ...],
    groups: list[list[int]],
) -> dict[str, Any]:
    """Independent feasibility validator for one-hot groups."""
    violations: list[dict[str, Any]] = []
    for g_idx, group in enumerate(groups):
        selected = sum(int(bits[i]) for i in group)
        if selected != 1:
            violations.append(
                {
                    "group_index": g_idx,
                    "variables": group,
                    "selected_count": selected,
                    "expected": 1,
                }
            )
    return {
        "feasible": len(violations) == 0,
        "violations": violations,
        "n_violations": len(violations),
    }


def suggest_penalty(max_abs_operational_cost: float, *, margin: float = 1.5) -> float:
    """Conservative penalty large enough to dominate operational costs, not enormous."""
    base = max(abs(float(max_abs_operational_cost)), 1.0)
    return float(margin * base)
