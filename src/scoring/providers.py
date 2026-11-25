"""Scoring interfaces for plan operational costs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ContextScoringProvider(ABC):
    """Interface for future Jev / ML wiring. Only Heuristic is functional in PoC v0.1."""

    @abstractmethod
    def score_plan(self, features: dict[str, Any]) -> dict[str, float]:
        raise NotImplementedError


class HeuristicScoringProvider(ContextScoringProvider):
    """Simplified physical/heuristic cost model — NOT calibrated on real data.

    fuel_cost = liters * fuel_price
    delay_risk = delay_probability * delay_penalty
    time_proxy = estimated_travel_time_minutes * time_value_brl_per_min
    operational_cost = fuel_cost + delay_risk + time_proxy
    """

    def __init__(self, *, time_value_brl_per_min: float = 0.5) -> None:
        self.time_value_brl_per_min = float(time_value_brl_per_min)

    def estimate_fuel_liters(
        self,
        *,
        distance_km: float,
        cargo_weight_kg: float,
        vehicle_weight_kg: float,
        average_gradient_pct: float,
        elevation_gain_m: float,
        base_l_per_100km: float = 28.0,
    ) -> float:
        mass_factor = 1.0 + (cargo_weight_kg + vehicle_weight_kg) / 40000.0
        grade_factor = 1.0 + max(average_gradient_pct, 0.0) / 100.0
        elev_factor = 1.0 + elevation_gain_m / 5000.0
        liters_per_km = (base_l_per_100km / 100.0) * mass_factor * grade_factor * elev_factor
        return float(distance_km * liters_per_km)

    def score_plan(self, features: dict[str, Any]) -> dict[str, float]:
        liters = float(
            features.get("fuel_consumption_liters")
            or self.estimate_fuel_liters(
                distance_km=float(features["distance_km"]),
                cargo_weight_kg=float(features["cargo_weight_kg"]),
                vehicle_weight_kg=float(features["vehicle_weight_kg"]),
                average_gradient_pct=float(features["average_gradient_pct"]),
                elevation_gain_m=float(features["elevation_gain_m"]),
            )
        )
        fuel_price = float(features["fuel_price_brl"])
        fuel_cost = liters * fuel_price
        delay_prob = float(features["delay_probability"])
        delay_penalty = float(features["delay_penalty_brl"])
        delay_risk = delay_prob * delay_penalty
        time_proxy = float(features["estimated_travel_time_minutes"]) * self.time_value_brl_per_min
        operational = fuel_cost + delay_risk + time_proxy
        return {
            "fuel_consumption_liters": liters,
            "fuel_cost_brl": fuel_cost,
            "delay_risk_brl": delay_risk,
            "time_proxy_brl": time_proxy,
            "operational_cost_brl": operational,
        }


class JevScoringProvider(ContextScoringProvider):
    """Placeholder — Jev integration is out of scope for PoC v0.1."""

    def score_plan(self, features: dict[str, Any]) -> dict[str, float]:
        raise NotImplementedError("JevScoringProvider is not implemented in PoC v0.1")


class MLScoringProvider(ContextScoringProvider):
    """Placeholder — ML calibration is out of scope for PoC v0.1."""

    def score_plan(self, features: dict[str, Any]) -> dict[str, float]:
        raise NotImplementedError("MLScoringProvider is not implemented in PoC v0.1")
