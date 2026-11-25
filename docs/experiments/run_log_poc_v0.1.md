# Run log — Quantum PoC v0.1

Registro da execução local completa após mitigação do hang no cenário D.

## Ambiente

| Item | Valor |
|---|---|
| Data (UTC) | 2026-11-25T18:01:45Z (rerun local completo) |
| Commit base | `ba3c1f0` (+ artefatos deste rerun) |
| Branch | `feature/quantum-poc-v0.1` |
| Host | MacBook Air M4, ARM64, 16 GB |
| Python | 3.13 (venv local) |
| Qiskit | 2.6.2 |
| Qiskit Aer | 0.18.4 |
| Qiskit IBM Runtime | 0.52.1 |
| `MPLCONFIGDIR` | `.mplconfig/` |

## Comandos executados (ordem)

```bash
export MPLCONFIGDIR="$PWD/.mplconfig"
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_classical.py
.venv/bin/python scripts/run_simulator.py
.venv/bin/python scripts/run_noisy_simulator.py
.venv/bin/python scripts/run_benchmark.py
.venv/bin/python scripts/run_ibm_quantum.py --dry-run
.venv/bin/python scripts/build_report_artifacts.py
```

## Resultados dos testes

- `pytest -q`: **20 passed**
- Warnings: deprecation `QAOAAnsatz`/`NLocal` (KI-04); SparseEfficiencyWarning do SciPy

## Experimentos

| Etapa | Status | Observação |
|---|---|---|
| Clássico (toy + cenário A) | completed | Ótimos 01/10 = R$ 610; guloso A+A = R$ 660 |
| QAOA ideal (p=1,2,3 × seeds) | completed | Melhor: p=2, seed=42, **P(ótimo)=1.0**, ⟨H⟩≈610.006 |
| Ruído Aer | completed | TVD sintético vs ideal ≈ 0.0232 |
| Benchmark A | completed | n=4, P(ótimo QAOA)≈0.196 |
| Benchmark B | completed | n=6, P(ótimo QAOA)≈0.027 |
| Benchmark C | completed | n=9, P(ótimo QAOA)=0.0 (budget leve) |
| Benchmark D | **classical_only** | n=12; QAOA **skipped** (KI-01 mitigado); clássico OK em segundos |
| Toy 2q no benchmark | completed | P(ótimo)=1.0 |
| IBM Runtime | dry_run | `credentials.available=false`; **nenhum job submetido** |
| Relatório | completed | `REPORT.md`, `manifest.json`, evidências v2.1 |

## Tempo aproximado do pipeline

~51 s (após mitigação do D). Antes da mitigação, o D sozinho excedia 10 minutos sem concluir.

## Artefatos gerados

Diretório: `results/quantum_poc_v0.1/`

- JSON/CSV: classical, simulator, noisy, ibm dry-run, benchmark, parameters, ising, qubo, environment, run_config, manifest, convergence_history
- Gráficos: ideal/noisy distributions, convergence, optimal probability, scaling, circuit depth, classical vs quantum, feasibility
- `hardware_distribution.png`: **not_run** (sem QPU)

## Separação explícita de conclusões

1. **Modelagem conjunta**: ganho R$ 50 (~7,58%) no toy — confirmado.
2. **Qualidade QAOA**: no toy 2q supera baseline uniforme 50% (chegou a 100% na melhor seed).
3. **Ruído**: TVD > 0; distribuição degrada vs ideal.
4. **Hardware IBM**: apenas dry-run; etapa física **não concluída**.
5. **Vantagem quântica computacional**: **não afirmada**.

## Execução IBM QPU (etapa 2)

Concluída em 2026-11-25T18:16Z. Detalhes: `ibm_qpu_run_poc_v0.1.md`.

- Job: `dc3ibmdhdvas73bnvcfg` / backend `ibm_kingston` / shots 4096
- P(ótimo) hardware ≈ 0.9646; TVD vs ideal ≈ 0.0354
- Credenciais em `credentials/` (não versionadas); CRN vazio → `open-instance`

## Recuperação posterior

```bash
python scripts/run_ibm_quantum.py --job-id dc3ibmdhdvas73bnvcfg
```
