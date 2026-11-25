# Known issues — Quantum PoC v0.1

Registro explícito de falhas e mitigações. Instâncias interrompidas **não** são reportadas como concluídas.

## KI-01 — Hang no cenário D (12 qubits)

| Campo | Valor |
|---|---|
| Sintoma | `scripts/run_benchmark.py` ficou sem progresso por >10 minutos no cenário D |
| Causa provável | QAOA local com `StatevectorEstimator` + `QAOAAnsatz` em 12 variáveis one-hot (4 veículos × 3 rotas); cada avaliação de ⟨H⟩ fica cara no laptop M4 16 GB |
| Evidência original | Execução abortada sem artefato útil; nenhum resultado D marcado como QAOA `completed` |
| Mitigação | Cenário D = `classical_only` (enumeração factível + guloso + uniforme). QAOA não executado. Timeout wall-clock em A–C |
| Revalidação | 2026-11-25T17:57Z — D concluiu em segundos com status `classical_only` / `qaoa_status=skipped` (ver `run_log_poc_v0.1.md`) |
| Status | **Mitigado e revalidado** |

## KI-02 — Abort do Matplotlib no sandbox

| Campo | Valor |
|---|---|
| Sintoma | `run_simulator.py` terminou com exit code 134 ao salvar gráficos |
| Causa | Diretório `~/.matplotlib` não gravável no ambiente sandbox |
| Mitigação | `MPLCONFIGDIR` apontando para `.mplconfig/` no projeto; diretório ignorado no git |
| Revalidação | Pipeline completo gerou PNGs em `results/quantum_poc_v0.1/charts/` |
| Status | **Mitigado e revalidado** |

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

## KI-05 — Credenciais IBM ausentes no dry-run

| Campo | Valor |
|---|---|
| Sintoma | `credentials.available=false` no dry-run |
| Impacto | Etapa física não iniciada; plano gerado sem submissão |
| Resolução | API key realocada para `credentials/ibm_apikey.json` (gitignored) e salva via `QiskitRuntimeService.save_account` |
| Nota | `crn.json` veio vazio; usou-se `open-instance` automática |
| Status | **Resolvido** — job `dc3ibmdhdvas73bnvcfg` em `ibm_kingston` concluído (P(ótimo)≈0.965) |

## KI-06 — Segredo temporariamente fora do cofre

| Campo | Valor |
|---|---|
| Sintoma | `apikey.json` / `crn.json` estavam em `experiments/02_qaoa_simulator/` (pasta versionável) |
| Mitigação | Movidos para `credentials/`; ignores reforçados; arquivos removidos da pasta de experimentos |
| Status | Mitigado |

## Política

- Timeout ou skip ⇒ status `interrupted` ou `classical_only`, nunca `completed` para a parte QAOA.
- Sem credenciais IBM ⇒ dry-run apenas; sem resultados inventados de QPU.
- Ver também: `run_log_poc_v0.1.md`, `results/quantum_poc_v0.1/REPORT.md`.
