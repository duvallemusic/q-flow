#!/usr/bin/env python3
"""Assemble manifest, REPORT.md and whitepaper evidence from generated results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.results_io import environment_snapshot, utc_now, write_json


OUT = ROOT / "results" / "quantum_poc_v0.1"
DOCS_EXP = ROOT / "docs" / "experiments"


def load(name: str):
    path = OUT / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def status_of(name: str) -> str:
    return "completed" if (OUT / name).exists() else "not_run"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS_EXP.mkdir(parents=True, exist_ok=True)

    classical = load("classical_results.json")
    simulator = load("simulator_results.json")
    noisy = load("noisy_simulator_results.json")
    ibm = load("ibm_quantum_results.json")
    bench = load("benchmark_results.json")
    params = load("optimized_parameters.json")
    env = environment_snapshot(ROOT)

    manifest = {
        "poc_version": "0.1",
        "created_at_utc": utc_now(),
        "git_commit": env.get("git_commit"),
        "artifacts": {
            "classical_results.json": status_of("classical_results.json"),
            "simulator_results.json": status_of("simulator_results.json"),
            "noisy_simulator_results.json": status_of("noisy_simulator_results.json"),
            "ibm_quantum_results.json": status_of("ibm_quantum_results.json"),
            "benchmark.csv": status_of("benchmark.csv"),
            "optimized_parameters.json": status_of("optimized_parameters.json"),
            "hardware_distribution.png": status_of("charts/hardware_distribution.png"),
        },
        "ibm_stage": {
            "local_ready": status_of("ibm_quantum_results.json") == "completed",
            "physical_execution": (
                "completed"
                if ibm and ibm.get("result", {}).get("status") == "completed"
                else "not_completed"
            ),
            "mode": None if not ibm else ibm.get("mode"),
        },
        "data_provenance": "synthetic / illustrative White Paper example",
    }
    write_json(OUT / "manifest.json", manifest)
    write_json(OUT / "environment.json", env)
    write_json(
        OUT / "run_config.json",
        {
            "python_constraint": ">=3.12,<3.14",
            "max_qaoa_qubits": 12,
            "default_shots": 4096,
            "optimizer": "COBYLA",
            "primitives": "StatevectorEstimator + StatevectorSampler (V2)",
            "ibm_default": "dry-run",
        },
    )

    selected = params or {}
    sim_note = "not_run"
    opt_prob = None
    if simulator:
        sim_note = "completed"
        opt_prob = selected.get("optimal_probability")

    noisy_tvd = None
    if noisy:
        noisy_tvd = noisy.get("synthetic_noise", {}).get("tvd_vs_ideal")

    ibm_status = "not_run"
    if ibm:
        ibm_status = ibm.get("mode", "unknown")
        if ibm.get("result", {}).get("status"):
            ibm_status = f"{ibm.get('mode')}:{ibm['result']['status']}"

    report = f"""# Q-Flow Quantum PoC v0.1 — REPORT

## 1. Resumo executivo

PoC local da camada de otimização clássica/quântica da Q-Flow para o Qiskit Fall Fest 2026.
O exemplo oficial de dois caminhões foi verificado por enumeração exata (ótimos degenerados em R$ 610).
QAOA foi treinado com primitives V2 do Qiskit (`StatevectorEstimator` / `StatevectorSampler`).
Execução em QPU física permanece separada e só é marcada como concluída com job real.

- Ganho de modelagem conjunta vs escolha ingênua 00: **R$ 50 (~7,58%)** — não é vantagem quântica.
- Melhor configuração local QAOA: p={selected.get('p')}, seed={selected.get('seed')}, P(ótimo)={opt_prob}.
- IBM: `{ibm_status}`.

## 2. Hipóteses

| ID | Hipótese | Classificação |
|---|---|---|
| H1 | Modelar interdependências reduz custo vs escolhas individuais | Confirmada no escopo experimental |
| H2 | QAOA ideal concentra probabilidade em ótimos melhor que amostragem uniforme no toy 2q | {'Parcialmente confirmada' if opt_prob is not None else 'Não testada'} |
| H3 | Ruído deprecia a distribuição em relação ao ideal | {'Parcialmente confirmada' if noisy_tvd is not None else 'Não testada'} |
| H4 | Execução física IBM é operacionalmente viável no toy 2q | Não testada / preparada em dry-run |
| H5 | Há vantagem computacional quântica vs clássico exato | Não confirmada (instância minúscula; clássico exato trivial) |

## 3. Metodologia

- QUBO → Ising via `x=(I-Z)/2`, operador `SparsePauliOp`.
- Baseline clássico: enumeração exata, guloso individual, amostragem uniforme, enumeração factível one-hot.
- QAOA: `QAOAAnsatz`, COBYLA, múltiplos restarts/seeds, p∈{{1,2,3}}.
- Ruído: Aer + depolarizing sintético e tentativa de fake backend.
- IBM: módulo isolado com dry-run obrigatório; `--execute` exige confirmação interativa.

## 4. Configuração experimental

Ver `environment.json` e `run_config.json`. Plataforma de desenvolvimento: MacBook Air M4 (ARM64), 16 GB.

## 5. Resultados matemáticos

Valores analíticos do White Paper reproduzidos: 00=660, 01=610, 10=610, 11=630.
Hamiltoniano: `627.5 I + 7.5 Z1 + 7.5 Z2 + 17.5 Z1 Z2`.

## 6. Resultados clássicos

Ver `classical_results.json`. O guloso individual no cenário A escolhe A+A (R$ 660); o ótimo conjunto factível é R$ 610.

## 7. Resultados da simulação QAOA

Status: {sim_note}. Detalhes em `simulator_results.json`.
Parâmetros exportados em `optimized_parameters.json`.

## 8. Resultados da simulação ruidosa

TVD (sintético vs ideal): {noisy_tvd}. Arquivo: `noisy_simulator_results.json`.
Não confundir com hardware real.

## 9. Resultados de hardware

Estado: {ibm_status}.
Nenhum resultado físico é inventado. Gráfico `hardware_distribution.png` só existe após job concluído.

## 10. Gráficos

Disponíveis em `charts/` conforme experimentos executados.

## 11. Análise

Separar quatro camadas de evidência:

1. **Modelagem**: ganho R$ 50 no toy.
2. **Qualidade QAOA**: probabilidade ótima vs baseline uniforme 50%.
3. **Ruído**: TVD e degradação de P(ótimo).
4. **Hardware**: somente com job IBM real.

## 12. Limitações

- Dados sintéticos / ilustrativos.
- Instâncias pequenas (≤12 qubits no laptop).
- Sem integração Jev/ML.
- Sem OR-Tools industrial; clássico exato via enumeração factível.
- Sem alegação de economia real de combustível ou cliente.

## 13. Falhas observadas

Ver `docs/experiments/known_issues_poc_v0.1.md`.

- **KI-01**: QAOA no cenário D (12 qubits) hangou >10 min no MacBook Air M4 16GB; mitigado com `classical_only` + timeout; **revalidado** (D conclui em segundos).
- **KI-02**: Matplotlib abortou no sandbox sem `MPLCONFIGDIR` gravável; revalidado com gráficos gerados.
- **KI-03**: Namespace Origin/Cursor indisponível; repositório hospedado no GitHub privado.
- **KI-04**: Deprecation warnings do `QAOAAnsatz`/`NLocal` no Qiskit 2.6.
- **KI-05**: IBM dry-run sem credenciais (`credentials.available=false`); nenhum job submetido.
- Log completo: `docs/experiments/run_log_poc_v0.1.md`.

## 14. Recomendações

1. Executar `--execute` apenas no toy 2q após revisar quota.
2. Ampliar benchmarks clássicos (MIP/CP-SAT) em v0.2.
3. Manter warm-start / Jev / ML para experimentos seguintes.

## 15. Conclusão

A etapa local da PoC v0.1 está concluída quando testes matemáticos, QAOA ideal, parâmetros persistidos e dry-run IBM passam.
A etapa física só conclui com recuperação de resultados de QPU.

## 16. Declaração de utilização de IA

Este código, experimentos e documentação da PoC v0.1 foram desenvolvidos com assistência de um agente de IA (Cursor) sob supervisão humana. Resultados numéricos foram gerados pelas bibliotecas instaladas e pelos scripts versionados; hipóteses não validadas permanecem explicitamente classificadas.
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")

    docs_report = report.replace(
        "# Q-Flow Quantum PoC v0.1 — REPORT",
        "# Q-Flow Quantum PoC v0.1 — Experiment Report\n\nCópia de trabalho em `docs/experiments/`. Artefatos numéricos em `results/quantum_poc_v0.1/`.",
    )
    (DOCS_EXP / "quantum_poc_v0.1.md").write_text(docs_report, encoding="utf-8")

    evidence = f"""# Evidências verificáveis para White Paper v2.1

Este arquivo contém apenas afirmações suportadas pelos artefatos da PoC v0.1.

## Verificação matemática (toy 2 caminhões)

- Função: `F=660-50x1-50x2+70x1x2`
- Valores: `00=660`, `01=610`, `10=610`, `11=630`
- Ótimos degenerados: `01` e `10`
- Ganho de modelagem vs baseline `00`: R$ 50 (~7,58%)
- Interpretação obrigatória: ganho de **modelagem conjunta**, não vantagem quântica

## Ising

- `H = 627.5 I + 7.5 Z1 + 7.5 Z2 + 17.5 Z1 Z2`
- Equivalência QUBO/Ising verificada por enumeração e testes automatizados

## QAOA (simulador ideal)

- Biblioteca: Qiskit {env.get('versions', {}).get('qiskit')}
- Melhor configuração local: p={selected.get('p')}, seed={selected.get('seed')}
- P(ótimo) observada: {opt_prob}
- Baseline uniforme teórico no toy: 50%
- Parâmetros em `results/quantum_poc_v0.1/optimized_parameters.json`

## Ruído

- TVD sintético vs ideal: {noisy_tvd}
- Simulação ruidosa ≠ QPU

## IBM Quantum

- Estado registrado: `{ibm_status}`
- Dry-run implementado; submissão real exige `--execute` + confirmação `EXECUTE`
- Credenciais locais nesta execução: ver `ibm_quantum_results.json` (`credentials.available`)

## Benchmark de escala (sintético)

- A/B/C: QAOA executado com budget limitado no laptop
- D (12 vars): somente clássico (`classical_only`) após hang documentado (KI-01)
- Fonte: `results/quantum_poc_v0.1/benchmark.csv` e `docs/experiments/run_log_poc_v0.1.md`

## O que NÃO entra no White Paper ainda

- Economia real de combustível
- Vantagem quântica computacional
- Integração Jev/ML
- Resultados de clientes
- Resultados de QPU física
"""
    (DOCS_EXP / "whitepaper_v2.1_evidence.md").write_text(evidence, encoding="utf-8")
    print("Wrote REPORT.md, docs/experiments/* and manifest.json")


if __name__ == "__main__":
    main()
