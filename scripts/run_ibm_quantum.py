#!/usr/bin/env python3
"""IBM Quantum Runtime entrypoint — dry-run by default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cdc.ising import qubo_to_ising
from src.cdc.qubo import two_truck_example
from src.optimization.ibm_runtime import dry_run, execute_on_ibm, fetch_job
from src.results_io import environment_snapshot, utc_now, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="IBM Quantum guarded runner for Q-Flow PoC")
    parser.add_argument("--dry-run", action="store_true", help="Plan execution without submitting")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Submit a real job (requires credentials and explicit approval)",
    )
    parser.add_argument("--job-id", type=str, default=None, help="Fetch an existing job; no new submit")
    parser.add_argument("--backend", type=str, default=None)
    parser.add_argument("--shots", type=int, default=4096)
    args = parser.parse_args()

    out = ROOT / "results" / "quantum_poc_v0.1"
    out.mkdir(parents=True, exist_ok=True)

    model = two_truck_example()
    ising = qubo_to_ising(model)
    params_path = out / "optimized_parameters.json"
    if params_path.exists():
        params = json.loads(params_path.read_text(encoding="utf-8"))
        parameters = params["final_parameters"]
        p = int(params["p"])
    else:
        # Safe fallback if simulator not run yet
        parameters = [0.5] * 4
        p = 2
        params = {"p": p, "final_parameters": parameters, "note": "fallback_initial_guess"}

    optima = set(model.metadata["optimal_bitstrings"])

    if args.job_id:
        record = fetch_job(
            args.job_id,
            n_qubits=model.n_vars,
            optimal_bitstrings=optima,
            cost_fn=model.evaluate,
        )
        payload = {
            "created_at_utc": utc_now(),
            "mode": "fetch_job",
            "environment": environment_snapshot(ROOT),
            "result": record,
        }
        write_json(out / "ibm_quantum_results.json", payload)
        print(json.dumps(record, indent=2))
        return

    if args.execute and args.dry_run:
        raise SystemExit("Choose either --dry-run or --execute, not both")

    if args.execute:
        confirm = input("Type EXECUTE to submit one IBM Quantum job: ").strip()
        if confirm != "EXECUTE":
            raise SystemExit("Aborted: confirmation not provided")
        record = execute_on_ibm(
            model,
            ising,
            parameters,
            p=p,
            shots=args.shots,
            backend_name=args.backend,
            confirm=True,
            optimal_bitstrings=optima,
            results_dir=out,
        )
        mode = "execute"
    else:
        record = dry_run(
            model,
            ising,
            parameters,
            p=p,
            shots=args.shots,
            backend_name=args.backend,
        )
        mode = "dry_run"

    payload = {
        "created_at_utc": utc_now(),
        "mode": mode,
        "parameters_source": params,
        "environment": environment_snapshot(ROOT),
        "result": record,
        "max_jobs": 1,
        "note": "Physical QPU results are recorded only when a real job completes.",
    }
    write_json(out / "ibm_quantum_results.json", payload)
    print(json.dumps(record, indent=2, default=str))


if __name__ == "__main__":
    main()
