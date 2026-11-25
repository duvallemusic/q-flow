# CDC — Contextual Decision Compiler

Implementação inicial da PoC v0.1:

- `qubo.py` — modelo QUBO e exemplo oficial de dois caminhões
- `ising.py` — conversão `x=(I-Z)/2` para `SparsePauliOp`
- `constraints.py` — penalidade one-hot e validador
- `compiler.py` — planos candidatos → QUBO/Ising + metadados
