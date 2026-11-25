#!/usr/bin/env python3
"""Benchmark de escala (cenarios A, B e C) com metricas do circuito transpilado.

Refaz o estudo do slide de limites com configuracao fixa e registrada, pra todo
numero do slide sair de um arquivo. Simulador ideal, p=1, codificacao one-hot.
Profundidade e CZ: transpilado para cz/rz/sx/x, sem mapa de acoplamento (sem roteamento).

Rodar na raiz do projeto:
  python scripts/run_scaling_benchmark.py
"""

from __future__ import annotations

import csv
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from scipy.sparse import SparseEfficiencyWarning

    warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)
except ImportError:  # pragma: no cover
    pass

from qiskit import transpile  # noqa: E402
from qiskit.circuit.library import QAOAAnsatz  # noqa: E402

from src.cdc.ising import cost_operator_without_identity, qubo_to_ising  # noqa: E402
from src.datasets.synthetic import generate_scenario  # noqa: E402
from src.optimization.benchmark import benchmark_instance  # noqa: E402
from src.optimization.classical import solve_classical_mip_like  # noqa: E402
from src.results_io import environment_snapshot, utc_now, write_json  # noqa: E402

CONFIG = {"p": 1, "shots": 4096, "seed": 42, "maxiter": 60, "n_restarts": 2, "timeout_seconds": 400.0}
SCENARIOS = ["A", "B", "C"]


def transpiled_metrics(compiled, p: int) -> dict:
    """Profundidade e numero de CZ do circuito, sem roteamento (todos com todos)."""
    ising = qubo_to_ising(compiled.qubo)
    circuit = QAOAAnsatz(cost_operator=cost_operator_without_identity(ising), reps=p)
    circuit = circuit.assign_parameters([0.1] * circuit.num_parameters)
    circuit.measure_all()
    tc = transpile(circuit, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=42)
    ops = tc.count_ops()
    return {"transpiled_depth": tc.depth(), "cz_count": int(ops.get("cz", 0))}


def main() -> int:
    out = ROOT / "results" / "scaling_benchmark_v0.2"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in SCENARIOS:
        _, compiled = generate_scenario(name)
        n = compiled.qubo.n_vars
        print(f"cenario {name}: {n} qubits...", flush=True)
        res = benchmark_instance(
            compiled,
            p=CONFIG["p"],
            shots=CONFIG["shots"],
            seed=CONFIG["seed"],
            run_noisy=False,
            max_qubits=12,
            maxiter=CONFIG["maxiter"],
            n_restarts=CONFIG["n_restarts"],
            run_qaoa_flag=True,
            qaoa_timeout_seconds=CONFIG["timeout_seconds"],
        )
        row = res.get("row", {})
        # acaso exato: otimos factiveis / 2^n (o arquivo antigo usava amostragem)
        n_opt = len(solve_classical_mip_like(compiled)["optima"])
        metrics = transpiled_metrics(compiled, CONFIG["p"])
        rows.append(
            {
                "scenario": name,
                "qubits": n,
                "feasible_solutions": row.get("number_of_feasible_solutions"),
                "qaoa_optimal_probability": row.get("qaoa_optimal_probability"),
                "uniform_optimal_probability_sampled": row.get("uniform_optimal_probability"),
                "n_optimal_bitstrings": n_opt,
                "uniform_optimal_probability_exact": n_opt / 2**n,
                "qaoa_feasibility_rate": row.get("qaoa_feasibility_rate"),
                "qaoa_status": row.get("qaoa_status") or res.get("status"),
                **metrics,
            }
        )
        print(f"  {rows[-1]}", flush=True)

    with (out / "benchmark.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_json(
        out / "benchmark.json",
        {"created_at_utc": utc_now(), "config": CONFIG, "environment": environment_snapshot(ROOT), "rows": rows},
    )
    print(f"salvo em {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
