# Evidências verificáveis para White Paper v2.1

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

- Biblioteca: Qiskit 2.6.2
- Melhor configuração local: p=2, seed=42
- P(ótimo) observada: 1.0
- Baseline uniforme teórico no toy: 50%
- Parâmetros em `results/quantum_poc_v0.1/optimized_parameters.json`

## Ruído

- TVD sintético vs ideal: 0.023193359375
- Simulação ruidosa ≠ QPU

## IBM Quantum

- Estado registrado: `dry_run:dry_run`
- Dry-run implementado; submissão real exige `--execute` + confirmação `EXECUTE`

## O que NÃO entra no White Paper ainda

- Economia real de combustível
- Vantagem quântica computacional
- Integração Jev/ML
- Resultados de clientes
