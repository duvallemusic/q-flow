# Q-Flow — Adaptive Logistics Intelligence

Proposta de startup B2B para o Qiskit Fall Fest 2026 (IBM + FIAP). Integra dados históricos, Jev, machine learning, otimização clássica e Qiskit.

**Estado atual (PoC v0.1 + Jev):** camada clássica/quântica implementada e testada (40 testes). Exemplo de dois bits verificado; QAOA ideal executado com primitives V2; ruído via Aer; QAOA executado no IBM Kingston (job `dc3ibmdhdvas73bnvcfg`) e, com o risco do Jev no QUBO, no IBM Fez (job `dc3ljc5s2omc738dr9ig`). Sem alegação de vantagem quântica nem economia real de combustível.

Repositório: https://github.com/duvallemusic/q-flow

## Documentação
- [White Paper v2.0 (PDF)](releases/whitepaper_v2.0.pdf)
- [Executive Summary v2.0 (PDF)](releases/executive_summary_v2.0.pdf)
- [Texto do White Paper](docs/whitepaper.md) e [resumo](docs/executive_summary.md)
- [Arquitetura](docs/architecture/overview.md) e [referências](docs/references.md)
- [PoC quântica v0.1](docs/experiments/quantum_poc_v0.1.md)
- [Evidências para White Paper v2.1](docs/experiments/whitepaper_v2.1_evidence.md)
- [Known issues](docs/experiments/known_issues_poc_v0.1.md)
- [Run log da PoC](docs/experiments/run_log_poc_v0.1.md)
- [Execução IBM QPU](docs/experiments/ibm_qpu_run_poc_v0.1.md)
- [Materiais iniciais do Challenge](docs/challenge/)

## Ambiente

```bash
# Python 3.12 ou 3.13 (testado com 3.13 em macOS ARM64)
python3.13 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
# ou: pip install -r requirements.lock.txt
export MPLCONFIGDIR="$PWD/.mplconfig"
```

Versões efetivas desta PoC (ver também `results/quantum_poc_v0.1/environment.json`):

- qiskit 2.6.2
- qiskit-aer 0.18.4
- qiskit-ibm-runtime 0.52.1

## Reproduzir

```bash
# Testes (sem quota IBM)
pytest -q

# Pipeline local
python scripts/run_classical.py
python scripts/run_simulator.py
python scripts/run_noisy_simulator.py
python scripts/run_benchmark.py
python scripts/run_ibm_quantum.py --dry-run
python scripts/build_report_artifacts.py

# IBM real (exige credenciais locais + confirmação interativa EXECUTE)
python scripts/run_ibm_quantum.py --execute
python scripts/run_ibm_quantum.py --job-id JOB_ID
```

Artefatos em `results/quantum_poc_v0.1/`.

## Replicar a prova Jev + IBM

Os números da apresentação saem destes arquivos:

| Resultado | Arquivo |
|---|---|
| IBM Kingston: 96,5% das medições no ótimo (job `dc3ibmdhdvas73bnvcfg`) | `results/quantum_poc_v0.1/ibm_quantum_results.json` |
| Jev (`jev-1.14.0`): risco de atraso 0,86 na rota A e 0,11 na rota B | `results/jev_poc_v0.1/jev_responses.json` |
| QUBO com o risco do Jev e decisão ótima | `results/jev_poc_v0.1/qubo_jev.json` |
| IBM Fez: 88,8% das medições no ótimo (job `dc3ljc5s2omc738dr9ig`) | `results/jev_poc_v0.1/ibm_results.json` |
| Benchmark de escala (4, 6 e 9 qubits) | `results/scaling_benchmark_v0.2/benchmark.json` |

```bash
# 1) Sem chave: testes e a mesma rodada usando as respostas salvas do Jev
pytest
cp -r results/jev_poc_v0.1 results/replica_jev
python scripts/run_jev_pipeline.py --reuse-jev --results-dir results/replica_jev

# 2) Com chaves em credentials/ (pasta ignorada pelo git): chama o Jev e a IBM de novo
python scripts/run_jev_pipeline.py --results-dir results/minha_rodada
python scripts/run_jev_pipeline.py --ibm-dry-run --results-dir results/minha_rodada
python scripts/run_jev_pipeline.py --ibm-execute --results-dir results/minha_rodada

# 3) Benchmark de escala no simulador (regrava results/scaling_benchmark_v0.2)
python scripts/run_scaling_benchmark.py
```

No PowerShell, troque o `cp -r` por `Copy-Item -Recurse results\jev_poc_v0.1 results\replica_jev`.

O que esperar: o QUBO (`F = 1520 - 425 x1 - 425 x2 + 70 x1x2`) e a decisão ótima (`11`) saem idênticos. No simulador, o melhor resultado foi 97,1% no Windows 11 e 96,6% no Linux; no hardware, cada job varia um pouco. Como criar os arquivos de chave: [experiments/04_jev_integration/README.md](experiments/04_jev_integration/README.md).

## Escopo da PoC v0.1
- CDC: QUBO, Ising (`SparsePauliOp`), one-hot, compilador de planos sintéticos
- Clássico: enumeração, guloso individual, uniforme, enumeração factível
- QAOA: `QAOAAnsatz` + `StatevectorEstimator`/`StatevectorSampler` (API V2)
- Ruído: Aer sintético + tentativa de fake backend
- IBM: dry-run obrigatório; `--execute` guarda submissão
- Cenário D (12 vars): apenas clássico (QAOA skipped — ver known issues)

Fora de escopo agora: ML calibrado, warm-start completo, ASR completo, piloto com cliente. O Jev real entrou na integração de `experiments/04_jev_integration/`.

## Governança
Não commitar telemetria de clientes, chaves, `.env` ou dados pessoais. Licença não definida.

## Transparência
ChatGPT, Cursor e Claude foram usados como apoio à pesquisa, modelagem, código, redação e diagramas. Os resultados numéricos saem dos scripts, da API do Jev e dos jobs da IBM, não da IA. Resultados não validados estão classificados nos relatórios.
