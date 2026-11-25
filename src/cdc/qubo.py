"""QUBO models for Q-Flow combinatorial decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any

import numpy as np


@dataclass
class QuboModel:
    """Quadratic unconstrained binary optimization model.

    Objective: F(x) = offset + Σ linear[i] x_i + Σ_{i<=j} quadratic[(i,j)] x_i x_j
    """

    n_vars: int
    linear: dict[int, float] = field(default_factory=dict)
    quadratic: dict[tuple[int, int], float] = field(default_factory=dict)
    offset: float = 0.0
    variable_names: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    scale: float = 1.0  # multiply costs by scale for variational work; 1.0 = reais

    def __post_init__(self) -> None:
        if not self.variable_names:
            self.variable_names = [f"x{i}" for i in range(self.n_vars)]
        if len(self.variable_names) != self.n_vars:
            raise ValueError("variable_names length must equal n_vars")
        normalized: dict[tuple[int, int], float] = {}
        for (i, j), coeff in self.quadratic.items():
            a, b = (i, j) if i <= j else (j, i)
            normalized[(a, b)] = normalized.get((a, b), 0.0) + float(coeff)
        self.quadratic = normalized

    def evaluate(self, x: list[int] | tuple[int, ...] | np.ndarray) -> float:
        bits = [int(v) for v in x]
        if len(bits) != self.n_vars:
            raise ValueError(f"expected {self.n_vars} bits, got {len(bits)}")
        value = float(self.offset)
        for i, coeff in self.linear.items():
            value += float(coeff) * bits[i]
        for (i, j), coeff in self.quadratic.items():
            value += float(coeff) * bits[i] * bits[j]
        return value

    def evaluate_operational(
        self, x: list[int] | tuple[int, ...] | np.ndarray, *, penalty_prefix: str = "penalty"
    ) -> float:
        """Evaluate ignoring metadata-marked penalty quadratic/linear terms when possible.

        Prefer using the compiler-provided operational_cost callback when available.
        Falls back to full QUBO value.
        """
        _ = penalty_prefix
        return self.evaluate(x)

    def to_dense_matrix(self) -> np.ndarray:
        """Return upper-triangular Q such that x^T Q x + offset ≈ F(x) for binary x.

        Diagonal holds linear coefficients; off-diagonal holds quadratic coeffs.
        """
        q = np.zeros((self.n_vars, self.n_vars), dtype=float)
        for i, coeff in self.linear.items():
            q[i, i] += float(coeff)
        for (i, j), coeff in self.quadratic.items():
            if i == j:
                q[i, i] += float(coeff)
            else:
                q[i, j] += float(coeff)
        return q

    def enumerate(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for bits in product([0, 1], repeat=self.n_vars):
            cost = self.evaluate(bits)
            rows.append(
                {
                    "bits": bits,
                    "bitstring": "".join(str(b) for b in bits),
                    "cost": cost,
                    "assignment": {
                        self.variable_names[i]: bits[i] for i in range(self.n_vars)
                    },
                }
            )
        return rows

    def optima(self) -> list[dict[str, Any]]:
        rows = self.enumerate()
        best = min(r["cost"] for r in rows)
        return [r for r in rows if np.isclose(r["cost"], best)]

    def scaled(self, factor: float) -> QuboModel:
        """Return a copy with costs multiplied by factor (for variational conditioning)."""
        return QuboModel(
            n_vars=self.n_vars,
            linear={i: c * factor for i, c in self.linear.items()},
            quadratic={k: c * factor for k, c in self.quadratic.items()},
            offset=self.offset * factor,
            variable_names=list(self.variable_names),
            metadata={**self.metadata, "scale_applied": factor, "parent_scale": self.scale},
            scale=self.scale * factor,
        )


def two_truck_example() -> QuboModel:
    """Official White Paper toy instance (fictional costs in BRL).

    F(x1,x2) = 660 - 50*x1 - 50*x2 + 70*x1*x2
    Analytical values: 00=660, 01=610, 10=610, 11=630.
    Two degenerate optima: 01 and 10.
    """
    return QuboModel(
        n_vars=2,
        linear={0: -50.0, 1: -50.0},
        quadratic={(0, 1): 70.0},
        offset=660.0,
        variable_names=["x1", "x2"],
        metadata={
            "instance_id": "two_truck_whitepaper",
            "currency": "BRL",
            "synthetic": True,
            "description": "Two trucks, routes A/B, congestion +70 when both choose A",
            "expected_values": {"00": 660, "01": 610, "10": 610, "11": 630},
            "optimal_bitstrings": ["01", "10"],
            "modeling_gain_vs_naive_00_brl": 50.0,
            "modeling_gain_pct_vs_660": 50.0 / 660.0 * 100.0,
        },
    )


def cost_two_truck(x1: int, x2: int) -> float:
    """Original White Paper expansion for the toy example."""
    return 660.0 - 50.0 * x1 - 50.0 * x2 + 70.0 * x1 * x2
