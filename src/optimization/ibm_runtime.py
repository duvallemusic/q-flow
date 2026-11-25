"""Guarded IBM Quantum Runtime execution (dry-run by default)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from src.cdc.ising import IsingHamiltonian, cost_operator_without_identity
from src.cdc.qubo import QuboModel
from src.optimization.qaoa import _counts_to_x_endian
from src.optimization.metrics import summarize_counts


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def credentials_available() -> dict[str, Any]:
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        # Prefer saved account; do not require env token in code.
        try:
            service = QiskitRuntimeService()
        except Exception:
            service = QiskitRuntimeService(channel="ibm_quantum_platform")
        backends = service.backends()
        operational = []
        for b in backends:
            try:
                status = b.status()
                operational.append(
                    {
                        "name": b.name,
                        "num_qubits": getattr(b.configuration(), "n_qubits", None)
                        if hasattr(b, "configuration")
                        else getattr(b, "num_qubits", None),
                        "operational": getattr(status, "operational", None),
                        "pending_jobs": getattr(status, "pending_jobs", None),
                        "status_msg": getattr(status, "status_msg", str(status)),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                operational.append({"name": getattr(b, "name", str(b)), "error": str(exc)})
        return {
            "available": True,
            "n_backends": len(backends),
            "backends": operational,
            "checked_at_utc": _utc_now(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "error": str(exc),
            "checked_at_utc": _utc_now(),
            "hint": "Configure local IBM Quantum credentials via QiskitRuntimeService.save_account or official CLI.",
        }


def build_execution_plan(
    model: QuboModel,
    ising: IsingHamiltonian,
    parameters: list[float],
    *,
    p: int,
    shots: int = 4096,
    backend_name: str | None = None,
) -> dict[str, Any]:
    circuit = QAOAAnsatz(cost_operator=cost_operator_without_identity(ising), reps=p)
    measured = circuit.assign_parameters(parameters)
    measured.measure_all()
    return {
        "dry_run": True,
        "created_at_utc": _utc_now(),
        "backend_name": backend_name or "UNSELECTED",
        "shots": shots,
        "p": p,
        "n_logical_qubits": model.n_vars,
        "parameter_names": [str(x) for x in circuit.parameters],
        "parameters": parameters,
        "logical_depth": measured.depth(),
        "logical_size": len(measured.data),
        "instance": model.metadata.get("instance_id"),
        "warning": "No job submitted. Pass --execute only after reviewing quota/cost.",
    }


def dry_run(
    model: QuboModel,
    ising: IsingHamiltonian,
    parameters: list[float],
    *,
    p: int,
    shots: int = 4096,
    backend_name: str | None = None,
) -> dict[str, Any]:
    creds = credentials_available()
    plan = build_execution_plan(
        model, ising, parameters, p=p, shots=shots, backend_name=backend_name
    )
    suggested = None
    if creds.get("available"):
        candidates = [
            b
            for b in creds.get("backends", [])
            if b.get("operational") and (b.get("num_qubits") or 0) >= model.n_vars
        ]
        if candidates:
            suggested = sorted(candidates, key=lambda b: b.get("pending_jobs") or 10**9)[0][
                "name"
            ]
            plan["backend_name"] = backend_name or suggested
    return {
        "status": "dry_run",
        "credentials": {"available": creds.get("available"), "n_backends": creds.get("n_backends")},
        "backends_preview": creds.get("backends", [])[:10],
        "suggested_backend": suggested,
        "plan": plan,
        "submitted": False,
        "job_id": None,
    }


def execute_on_ibm(
    model: QuboModel,
    ising: IsingHamiltonian,
    parameters: list[float],
    *,
    p: int,
    shots: int = 4096,
    backend_name: str | None = None,
    optimization_level: int = 1,
    confirm: bool = False,
    optimal_bitstrings: set[str] | None = None,
    results_dir: Path | None = None,
) -> dict[str, Any]:
    if not confirm:
        raise RuntimeError("Refusing IBM submission without confirm=True / --execute")

    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService()
    if backend_name is None:
        preview = dry_run(model, ising, parameters, p=p, shots=shots)
        backend_name = preview.get("suggested_backend")
        if not backend_name:
            raise RuntimeError("No suitable operational backend found")
    backend = service.backend(backend_name)

    circuit = QAOAAnsatz(cost_operator=cost_operator_without_identity(ising), reps=p)
    measured = circuit.assign_parameters(parameters)
    measured.measure_all()
    pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend)
    isa = pm.run(measured)

    plan = {
        "backend_name": backend_name,
        "shots": shots,
        "p": p,
        "logical_depth": measured.depth(),
        "transpiled_depth": isa.depth(),
        "transpiled_size": len(isa.data),
        "layout": str(getattr(isa, "layout", None)),
        "created_at_utc": _utc_now(),
    }
    print(json.dumps({"execution_plan": plan}, indent=2))

    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa], shots=shots)
    job_id = job.job_id()
    record: dict[str, Any] = {
        "status": "submitted",
        "job_id": job_id,
        "plan": plan,
        "submitted_at_utc": _utc_now(),
        "execution_type": "ibm_qpu",
    }
    if results_dir is not None:
        results_dir.mkdir(parents=True, exist_ok=True)
        (results_dir / "ibm_job_submitted.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )

    # Do not invent results; try to fetch if already done, else mark pending.
    try:
        status = job.status()
        record["remote_status"] = str(status)
        if str(status).upper() in {"DONE", "COMPLETED"} or getattr(status, "name", "") == "DONE":
            result = job.result()
            raw = result[0].data.meas.get_counts()
            counts = _counts_to_x_endian(raw, model.n_vars)
            summary = summarize_counts(
                counts,
                optimal_bitstrings=optimal_bitstrings or set(),
                cost_fn=model.evaluate,
            )
            record.update({"status": "completed", "counts": counts, **summary})
        else:
            record["status"] = "pending"
    except Exception as exc:  # noqa: BLE001
        record["status"] = "pending_or_error"
        record["error"] = str(exc)
    return record


def fetch_job(
    job_id: str,
    *,
    n_qubits: int,
    optimal_bitstrings: set[str] | None = None,
    cost_fn=None,
) -> dict[str, Any]:
    """Recover an existing job without submitting a new one."""
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    job = service.job(job_id)
    status = str(job.status())
    record: dict[str, Any] = {
        "job_id": job_id,
        "remote_status": status,
        "fetched_at_utc": _utc_now(),
        "submitted": False,
        "new_job_created": False,
    }
    done_tokens = {"DONE", "COMPLETED"}
    if status.upper() in done_tokens or "DONE" in status.upper():
        result = job.result()
        raw = result[0].data.meas.get_counts()
        counts = _counts_to_x_endian(raw, n_qubits)
        summary = summarize_counts(
            counts,
            optimal_bitstrings=optimal_bitstrings or set(),
            cost_fn=cost_fn,
        )
        record.update({"status": "completed", "counts": counts, **summary})
    elif "ERROR" in status.upper() or "FAILED" in status.upper() or "CANCEL" in status.upper():
        record["status"] = "failed"
        try:
            record["error"] = str(job.error_message())
        except Exception as exc:  # noqa: BLE001
            record["error"] = str(exc)
    else:
        record["status"] = "pending"
    return record
