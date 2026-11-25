"""Reproducible synthetic logistics scenarios."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from src.cdc.compiler import CandidatePlan, CompiledDecision, compile_instance
from src.scoring.providers import HeuristicScoringProvider

SCENARIO_SPECS: dict[str, dict[str, Any]] = {
    "A": {"n_vehicles": 2, "n_routes": 2, "seed": 42},
    "B": {"n_vehicles": 3, "n_routes": 2, "seed": 123},
    "C": {"n_vehicles": 3, "n_routes": 3, "seed": 2026},
    "D": {"n_vehicles": 4, "n_routes": 3, "seed": 7},
    "E": {"n_vehicles": 6, "n_routes": 3, "seed": 99},
}


def list_scenarios() -> list[str]:
    return list(SCENARIO_SPECS)


def _instance_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def generate_scenario(
    name: str,
    *,
    conflict_penalty_brl: float = 70.0,
    use_whitepaper_costs_for_a: bool = True,
) -> tuple[list[CandidatePlan], CompiledDecision]:
    if name not in SCENARIO_SPECS:
        raise KeyError(f"unknown scenario {name}; choose from {list_scenarios()}")
    spec = SCENARIO_SPECS[name]
    n_vehicles = int(spec["n_vehicles"])
    n_routes = int(spec["n_routes"])
    seed = int(spec["seed"])
    rng = np.random.default_rng(seed)
    scorer = HeuristicScoringProvider(time_value_brl_per_min=0.5)

    # Scenario A can reproduce the White Paper numerical example exactly.
    if name == "A" and use_whitepaper_costs_for_a:
        plans = [
            CandidatePlan(
                vehicle_id="truck_1",
                route_id="A",
                distance_km=100,
                cargo_weight_kg=10000,
                vehicle_weight_kg=8000,
                average_gradient_pct=2.0,
                elevation_gain_m=200,
                fuel_consumption_liters=30.0,
                fuel_price_brl=6.0,
                estimated_travel_time_minutes=120,
                delay_probability=0.1,
                delay_penalty_brl=100,
                operational_cost_brl=300.0,
                shared_resource_id="resource_A",
                metadata={"whitepaper_fixed": True},
            ),
            CandidatePlan(
                vehicle_id="truck_1",
                route_id="B",
                distance_km=110,
                cargo_weight_kg=10000,
                vehicle_weight_kg=8000,
                average_gradient_pct=1.0,
                elevation_gain_m=100,
                fuel_consumption_liters=32.0,
                fuel_price_brl=6.0,
                estimated_travel_time_minutes=130,
                delay_probability=0.05,
                delay_penalty_brl=100,
                operational_cost_brl=320.0,
                shared_resource_id="resource_B",
                metadata={"whitepaper_fixed": True},
            ),
            CandidatePlan(
                vehicle_id="truck_2",
                route_id="A",
                distance_km=95,
                cargo_weight_kg=9000,
                vehicle_weight_kg=8000,
                average_gradient_pct=2.0,
                elevation_gain_m=180,
                fuel_consumption_liters=29.0,
                fuel_price_brl=6.0,
                estimated_travel_time_minutes=115,
                delay_probability=0.1,
                delay_penalty_brl=100,
                operational_cost_brl=290.0,
                shared_resource_id="resource_A",
                metadata={"whitepaper_fixed": True},
            ),
            CandidatePlan(
                vehicle_id="truck_2",
                route_id="B",
                distance_km=105,
                cargo_weight_kg=9000,
                vehicle_weight_kg=8000,
                average_gradient_pct=1.0,
                elevation_gain_m=90,
                fuel_consumption_liters=31.0,
                fuel_price_brl=6.0,
                estimated_travel_time_minutes=125,
                delay_probability=0.05,
                delay_penalty_brl=100,
                operational_cost_brl=310.0,
                shared_resource_id="resource_B",
                metadata={"whitepaper_fixed": True},
            ),
        ]
        compiled = compile_instance(
            plans,
            instance_id="scenario_A_whitepaper",
            conflict_penalty_brl=70.0,
            one_hot_penalty_value=200.0,
        )
        return plans, compiled

    plans: list[CandidatePlan] = []
    route_labels = [chr(ord("A") + i) for i in range(n_routes)]
    # Shared resources: first route tends to congest a common corridor.
    for v in range(n_vehicles):
        vehicle_id = f"truck_{v+1}"
        vehicle_weight = float(rng.uniform(7000, 9000))
        cargo = float(rng.uniform(8000, 14000))
        for r_idx, route_id in enumerate(route_labels):
            distance = float(rng.uniform(80, 140))
            gradient = float(rng.uniform(0.5, 6.0))
            elev = float(rng.uniform(50, 600))
            fuel_price = float(rng.uniform(5.5, 6.5))
            delay_prob = float(rng.uniform(0.02, 0.25))
            delay_penalty = float(rng.uniform(80, 200))
            travel_min = distance / float(rng.uniform(0.6, 0.9))
            features = {
                "distance_km": distance,
                "cargo_weight_kg": cargo,
                "vehicle_weight_kg": vehicle_weight,
                "average_gradient_pct": gradient,
                "elevation_gain_m": elev,
                "fuel_price_brl": fuel_price,
                "estimated_travel_time_minutes": travel_min,
                "delay_probability": delay_prob,
                "delay_penalty_brl": delay_penalty,
            }
            scored = scorer.score_plan(features)
            shared = f"corridor_{route_id}" if r_idx == 0 else f"alt_{route_id}_{v}"
            plans.append(
                CandidatePlan(
                    vehicle_id=vehicle_id,
                    route_id=route_id,
                    distance_km=distance,
                    cargo_weight_kg=cargo,
                    vehicle_weight_kg=vehicle_weight,
                    average_gradient_pct=gradient,
                    elevation_gain_m=elev,
                    fuel_consumption_liters=scored["fuel_consumption_liters"],
                    fuel_price_brl=fuel_price,
                    estimated_travel_time_minutes=travel_min,
                    delay_probability=delay_prob,
                    delay_penalty_brl=delay_penalty,
                    operational_cost_brl=scored["operational_cost_brl"],
                    shared_resource_id=shared,
                    metadata={"scenario": name, "seed": seed, "heuristic": True},
                )
            )

    instance_id = f"scenario_{name}_seed{seed}"
    compiled = compile_instance(
        plans,
        instance_id=instance_id,
        conflict_penalty_brl=conflict_penalty_brl,
    )
    payload = {"scenario": name, "seed": seed, "plans": [asdict(p) for p in plans]}
    compiled.metadata["instance_hash"] = _instance_hash(payload)
    return plans, compiled


def save_scenario_json(name: str, out_dir: Path) -> Path:
    plans, compiled = generate_scenario(name)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"scenario_{name}.json"
    path.write_text(
        json.dumps(
            {
                "scenario": name,
                "plans": [asdict(p) for p in plans],
                "compiled": compiled.to_serializable(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path
