# Known issues — Quantum PoC v0.1

Registro explícito de falhas e mitigações. Instâncias interrompidas **não** são reportadas como concluídas.

## KI-01 — Hang no cenário D (12 qubits)

| Campo | Valor |
|---|---|
| Sintoma | `scripts/run_benchmark.py` ficou sem progresso por >10 minutos no cenário D |
| Causa provável | QAOA local com `StatevectorEstimator` + `QAOAAnsatz` em 12 variáveis one-hot (4 veículos × 3 rotas); cada avaliação de ⟨H⟩ fica cara no laptop M4 16 GB |
| Evidência | Execução abortada sem artefato `benchmark.csv`; nenhum resultado D marcado como `completed` |
| Mitigação | Cenário D passa a `classical_only` (enumeração factível + guloso + uniforme). QAOA não é executado. Timeout wall-clock adicionado para A–C |
| Status | Mitigado em `feature/quantum-poc-v0.1` |

## KI-02 — Abort do Matplotlib no sandbox

| Campo | Valor |
|---|---|
| Sintoma | `run_simulator.py` terminou com exit code 134 ao salvar gráficos |
| Causa | Diretório `~/.matplotlib` não gravável no ambiente sandbox |
| Mitigação | `MPLCONFIGDIR` apontando para `.mplconfig/` no projeto; diretório ignorado no git |
| Status | Mitigado |

## KI-03 — Namespace Origin (Cursor) indisponível

| Campo | Valor |
|---|---|
| Sintoma | `origin repo create` falhou: conta sem namespace Origin |
| Mitigação | Projeto publicado em GitHub privado: https://github.com/duvallemusic/q-flow |
| Status | Contornado (host GitHub) |

## KI-04 — Deprecation `QAOAAnsatz` / `NLocal`

| Campo | Valor |
|---|---|
| Sintoma | Warnings Qiskit 2.6: `NLocal` / `BlueprintCircuit` deprecated for Qiskit 3.0 |
| Impacto | Cosmético nesta PoC; API ainda funcional |
| Próximo passo | Migrar para a função equivalente em `qiskit.circuit.library.n_local` na v0.2 |
| Status | Aceito / documentado |

## Política

- Timeout ou skip ⇒ status `interrupted` ou `classical_only`, nunca `completed` para a parte QAOA.
- Sem credenciais IBM ⇒ dry-run apenas; sem resultados inventados de QPU.
