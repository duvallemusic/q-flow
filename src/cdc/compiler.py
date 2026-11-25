"""Contextual Decision Compiler — structured plans → QUBO/Ising."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .constraints import one_hot_penalty, suggest_penalty, validate_one_hot
from .ising import IsingHamiltonian, qubo_to_ising
from .qubo import QuboModel


@dataclass
class CandidatePlan:
    vehicle_id: str
    route_id: str
    distance_km: float
    cargo_weight_kg: float
    vehicle_weight_kg: float
    average_gradient_pct: float
    elevation_gain_m: float
    fuel_consumption_liters: float
    fuel_price_brl: float
    estimated_travel_time_minutes: float
    delay_probability: float
    delay_penalty_brl: float
    operational_cost_brl: float
    shared_resource_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompiledDecision:
    qubo: QuboModel
    ising: IsingHamiltonian
    variable_map: list[dict[str, Any]]
    groups: list[list[int]]
    plans: list[CandidatePlan]
    penalty: float
    normalization_scale: float
    operational_cost_fn: Callable[[list[int] | tuple[int, ...]], float]
    metadata: dict[str, Any]

    def validate(self, bits: list[int] | tuple[int, ...]) -> dict[str, Any]:
        return validate_one_hot(bits, self.groups)

    def operational_cost(self, bits: list[int] | tuple[int, ...]) -> float:
        return float(self.operational_cost_fn(bits))

    def to_serializable(self) -> dict[str, Any]:
        return {
            "n_vars": self.qubo.n_vars,
            "variable_names": self.qubo.variable_names,
            "linear": {str(k): v for k, v in self.qubo.linear.items()},
            "quadratic": {f"{i},{j}": v for (i, j), v in self.qubo.quadratic.items()},
            "offset": self.qubo.offset,
            "penalty": self.penalty,
            "normalization_scale": self.normalization_scale,
            "variable_map": self.variable_map,
            "groups": self.groups,
            "ising_paulis": [
                {"label": label, "coeff": [c.real, c.imag]}
                for label, c in zip(
                    self.ising.operator.paulis.to_labels(),
                    self.ising.operator.coeffs,
                    strict=True,
                )
            ],
            "ising_offset": self.ising.offset,
            "plans": [asdict(p) for p in self.plans],
            "metadata": self.metadata,
        }


def compile_instance(
    plans: list[CandidatePlan],
    *,
    instance_id: str,
    conflict_penalty_brl: float | None = None,
    one_hot_penalty_value: float | None = None,
    normalization_scale: float = 1.0,
) -> CompiledDecision:
    """Compile candidate vehicle plans into a QUBO with one-hot constraints.

    Operational cost for a feasible assignment is the sum of selected plan costs
    plus pairwise conflict penalties when two selected plans share a resource.
    """
    if not plans:
        raise ValueError("plans must be non-empty")

    by_vehicle: dict[str, list[int]] = {}
    variable_map: list[dict[str, Any]] = []
    for idx, plan in enumerate(plans):
        by_vehicle.setdefault(plan.vehicle_id, []).append(idx)
        variable_map.append(
            {
                "index": idx,
                "name": f"{plan.vehicle_id}__{plan.route_id}",
                "vehicle_id": plan.vehicle_id,
                "route_id": plan.route_id,
                "operational_cost_brl": plan.operational_cost_brl,
                "shared_resource_id": plan.shared_resource_id,
            }
        )

    groups = list(by_vehicle.values())
    for vehicle_id, idxs in by_vehicle.items():
        if len(idxs) < 1:
            raise ValueError(f"vehicle {vehicle_id} has no plans")

    # Pairwise conflict coefficients (added when both binary vars are 1).
    conflict_pairs: dict[tuple[int, int], float] = {}
    if conflict_penalty_brl is None:
        conflict_penalty_brl = 70.0
    resource_to_idxs: dict[str, list[int]] = {}
    for idx, plan in enumerate(plans):
        if plan.shared_resource_id:
            resource_to_idxs.setdefault(plan.shared_resource_id, []).append(idx)
    for idxs in resource_to_idxs.values():
        for a_i, i in enumerate(idxs):
            for j in idxs[a_i + 1 :]:
                # Only penalize conflicts across different vehicles.
                if plans[i].vehicle_id == plans[j].vehicle_id:
                    continue
                a, b = (i, j) if i < j else (j, i)
                conflict_pairs[(a, b)] = conflict_pairs.get((a, b), 0.0) + float(
                    conflict_penalty_brl
                )

    max_op = max(abs(p.operational_cost_brl) for p in plans)
    max_conflict = max(conflict_pairs.values()) if conflict_pairs else 0.0
    if one_hot_penalty_value is None:
        one_hot_penalty_value = suggest_penalty(max_op + max_conflict, margin=1.5)

    linear: dict[int, float] = {i: float(plans[i].operational_cost_brl) for i in range(len(plans))}
    quadratic: dict[tuple[int, int], float] = dict(conflict_pairs)
    offset = 0.0

    pen_lin, pen_quad, pen_off = one_hot_penalty(groups, penalty=one_hot_penalty_value)
    for i, c in pen_lin.items():
        linear[i] = linear.get(i, 0.0) + c
    for k, c in pen_quad.items():
        quadratic[k] = quadratic.get(k, 0.0) + c
    offset += pen_off

    names = [m["name"] for m in variable_map]
    qubo = QuboModel(
        n_vars=len(plans),
        linear=linear,
        quadratic=quadratic,
        offset=offset,
        variable_names=names,
        metadata={
            "instance_id": instance_id,
            "synthetic": True,
            "penalty": one_hot_penalty_value,
            "conflict_penalty_brl": conflict_penalty_brl,
            "currency": "BRL",
        },
        scale=1.0,
    )
    if normalization_scale != 1.0:
        qubo = qubo.scaled(normalization_scale)

    def operational_cost_fn(bits: list[int] | tuple[int, ...]) -> float:
        total = 0.0
        selected = [i for i, b in enumerate(bits) if int(b) == 1]
        for i in selected:
            total += float(plans[i].operational_cost_brl)
        for a_i, i in enumerate(selected):
            for j in selected[a_i + 1 :]:
                a, b = (i, j) if i < j else (j, i)
                total += float(conflict_pairs.get((a, b), 0.0))
        return total

    ising = qubo_to_ising(qubo)
    return CompiledDecision(
        qubo=qubo,
        ising=ising,
        variable_map=variable_map,
        groups=groups,
        plans=plans,
        penalty=float(one_hot_penalty_value),
        normalization_scale=float(normalization_scale),
        operational_cost_fn=operational_cost_fn,
        metadata={
            "instance_id": instance_id,
            "n_vehicles": len(by_vehicle),
            "n_plans": len(plans),
            "n_conflict_pairs": len(conflict_pairs),
        },
    )
