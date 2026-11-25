# Changelog

## v0.1.0-poc — 2026-11-25
- PoC quântica local: CDC (QUBO/Ising/constraints/compiler), baselines clássicos e QAOA V2.
- Experimentos ideal/ruidoso, benchmark sintético A–D, dry-run IBM Runtime.
- Execução física IBM no toy 2q: job `dc3ibmdhdvas73bnvcfg` em `ibm_kingston` (P(ótimo)≈0.965).
- Credenciais movidas para `credentials/` (gitignored); CRN vazio → open-instance.
- Artefatos em `results/quantum_poc_v0.1/` e evidências para White Paper v2.1.
- Known issue: QAOA no cenário D (12 qubits) skipped após hang; timeout wall-clock adicionado.
- Dependências: Python 3.13, Qiskit 2.6.2, Aer 0.18.4, IBM Runtime 0.52.1.

## v2.0 — 2026-11-25
- White Paper com arquitetura, QUBO/Ising, aprendizado, memória e Data Partnership.
- Executive Summary de três páginas.
- Repositório inicial, transcrições editáveis e materiais anteriores do Challenge.
- Enumeração clássica e teste de equivalência Ising do exemplo fictício.

## Próximas versões (planejadas)
- v2.1: incorporar evidências verificáveis da PoC ao White Paper.
- v2.2: QPU IBM (após job físico recuperado).
- v2.3: integração Jev.
- v2.4: calibração ML.
- v2.5: benchmark integrado com MIP/CP-SAT.
- v3.0: piloto real.
