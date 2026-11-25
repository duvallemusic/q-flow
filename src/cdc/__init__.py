"""Contextual Decision Compiler (CDC)."""

from .compiler import compile_instance
from .constraints import one_hot_penalty, validate_one_hot
from .ising import qubo_to_ising
from .qubo import QuboModel, two_truck_example

__all__ = [
    "QuboModel",
    "two_truck_example",
    "qubo_to_ising",
    "one_hot_penalty",
    "validate_one_hot",
    "compile_instance",
]
