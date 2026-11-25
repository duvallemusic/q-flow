"""Mathematical validation for QUBO/Ising and constraints."""

from __future__ import annotations

from itertools import product

import numpy as np
import pytest

from src.cdc.constraints import one_hot_penalty, validate_one_hot
from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import QuboModel, two_truck_example


def test_two_truck_expansion_values():
    model = two_truck_example()
    values = [model.evaluate(x) for x in product([0, 1], repeat=2)]
    assert values == [660, 610, 610, 630]


def test_two_truck_degenerate_optima():
    optima = two_truck_example().optima()
    bits = sorted(o["bitstring"] for o in optima)
    assert bits == ["01", "10"]
    assert all(np.isclose(o["cost"], 610) for o in optima)


def test_ising_equivalence_two_truck():
    model = two_truck_example()
    ising = qubo_to_ising(model)
    assert np.isclose(ising.offset, 627.5)
    assert np.isclose(ising.linear_z[0], 7.5)
    assert np.isclose(ising.linear_z[1], 7.5)
    assert np.isclose(ising.quadratic_zz[(0, 1)], 17.5)
    for bits in product([0, 1], repeat=2):
        assert np.isclose(model.evaluate(bits), ising.energy_from_bits(bits))


def test_asymmetric_three_variable_ising():
    """Asymmetric instance catches endianness / double-counting bugs."""
    model = QuboModel(
        n_vars=3,
        linear={0: -3.0, 1: 5.0, 2: -1.5},
        quadratic={(0, 1): 2.0, (0, 2): -4.0, (1, 2): 1.25},
        offset=10.0,
        variable_names=["a", "b", "c"],
    )
    ising = qubo_to_ising(model)
    for bits in product([0, 1], repeat=3):
        assert np.isclose(model.evaluate(bits), ising.energy_from_bits(bits), atol=1e-9)


def test_no_double_counting_quadratic():
    model = QuboModel(n_vars=2, linear={}, quadratic={(0, 1): 4.0, (1, 0): 6.0}, offset=0.0)
    # constructor merges (0,1) and (1,0)
    assert np.isclose(model.quadratic[(0, 1)], 10.0)
    assert (1, 0) not in model.quadratic


def test_normalization_scale_documented():
    model = two_truck_example().scaled(0.01)
    assert np.isclose(model.scale, 0.01)
    assert np.isclose(model.evaluate((0, 0)), 6.60)
    # Original reais recovered by dividing by scale
    assert np.isclose(model.evaluate((0, 1)) / model.scale, 610.0)


def test_one_hot_penalty_and_validator():
    groups = [[0, 1], [2, 3]]
    linear, quadratic, offset = one_hot_penalty(groups, penalty=10.0)
    model = QuboModel(n_vars=4, linear=linear, quadratic=quadratic, offset=offset)
    # Valid assignment: 1001
    assert np.isclose(model.evaluate([1, 0, 0, 1]), 0.0)
    assert validate_one_hot([1, 0, 0, 1], groups)["feasible"]
    assert not validate_one_hot([1, 1, 0, 1], groups)["feasible"]
    # Invalid should have positive penalty energy
    assert model.evaluate([1, 1, 0, 1]) > 0
