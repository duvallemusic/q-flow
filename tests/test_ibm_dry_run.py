"""IBM module tests — never submit remote jobs."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import two_truck_example
from src.optimization.ibm_runtime import build_execution_plan, dry_run, execute_on_ibm


def test_dry_run_does_not_submit():
    model = two_truck_example()
    ising = qubo_to_ising(model)
    with patch("src.optimization.ibm_runtime.credentials_available", return_value={"available": False}):
        result = dry_run(model, ising, [0.1, 0.2, 0.3, 0.4], p=2, shots=128)
    assert result["submitted"] is False
    assert result["job_id"] is None
    assert result["status"] == "dry_run"


def test_execute_requires_confirm():
    model = two_truck_example()
    ising = qubo_to_ising(model)
    try:
        execute_on_ibm(model, ising, [0.1, 0.2], p=1, confirm=False)
        assert False, "should have raised"
    except RuntimeError as exc:
        assert "confirm" in str(exc).lower()


def test_build_plan_metadata():
    model = two_truck_example()
    plan = build_execution_plan(
        model, qubo_to_ising(model), [0.2, 0.3], p=1, shots=1024, backend_name="fake"
    )
    assert plan["dry_run"] is True
    assert plan["n_logical_qubits"] == 2
    assert plan["shots"] == 1024


def test_credentials_probe_is_mocked_locally():
    with patch("src.optimization.ibm_runtime.credentials_available") as mocked:
        mocked.return_value = {"available": False, "error": "no creds"}
        from src.optimization.ibm_runtime import credentials_available

        assert credentials_available()["available"] is False
