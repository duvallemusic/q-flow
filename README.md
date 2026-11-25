# Q-Flow — Adaptive Logistics Intelligence

Proposta de startup B2B para o Qiskit Fall Fest 2026 (IBM + FIAP). Integra dados históricos, Jev, machine learning, otimização clássica e Qiskit.

**Estado atual (PoC v0.1):** camada clássica/quântica local implementada e testada. Exemplo de dois bits verificado; QAOA ideal executado com primitives V2; ruído via Aer; IBM preparado em dry-run. Sem alegação de vantagem quântica nem economia real de combustível.

Repositório: https://github.com/duvallemusic/q-flow

## Documentação
- [White Paper v2.0 (PDF)](releases/whitepaper_v2.0.pdf)
- [Executive Summary v2.0 (PDF)](releases/executive_summary_v2.0.pdf)
- [Texto do White Paper](docs/whitepaper.md) e [resumo](docs/executive_summary.md)
- [Arquitetura](docs/architecture/overview.md) e [referências](docs/references.md)
- [PoC quântica v0.1](docs/experiments/quantum_poc_v0.1.md)
- [Evidências para White Paper v2.1](docs/experiments/whitepaper_v2.1_evidence.md)
- [Known issues](docs/experiments/known_issues_poc_v0.1.md)
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

## Escopo da PoC v0.1
- CDC: QUBO, Ising (`SparsePauliOp`), one-hot, compilador de planos sintéticos
- Clássico: enumeração, guloso individual, uniforme, enumeração factível
- QAOA: `QAOAAnsatz` + `StatevectorEstimator`/`StatevectorSampler` (API V2)
- Ruído: Aer sintético + tentativa de fake backend
- IBM: dry-run obrigatório; `--execute` guarda submissão
- Cenário D (12 vars): apenas clássico (QAOA skipped — ver known issues)

Fora de escopo agora: Jev real, ML calibrado, warm-start completo, ASR completo, piloto com cliente.

## Governança
Não commitar telemetria de clientes, chaves, `.env` ou dados pessoais. Repositório privado. Licença não definida.

## Transparência
ChatGPT/Cursor foram usados como apoio à pesquisa, modelagem, código, redação e diagramas. Resultados não validados estão classificados nos relatórios.
