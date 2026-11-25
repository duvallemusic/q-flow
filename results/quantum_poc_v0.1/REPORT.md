# Q-Flow Quantum PoC v0.1 — REPORT

## 1. Resumo executivo

PoC local da camada de otimização clássica/quântica da Q-Flow para o Qiskit Fall Fest 2026.
O exemplo oficial de dois caminhões foi verificado por enumeração exata (ótimos degenerados em R$ 610).
QAOA foi treinado com primitives V2 do Qiskit (`StatevectorEstimator` / `StatevectorSampler`).
Execução em QPU física permanece separada e só é marcada como concluída com job real.

- Ganho de modelagem conjunta vs escolha ingênua 00: **R$ 50 (~7,58%)** — não é vantagem quântica.
- Melhor configuração local QAOA: p=2, seed=42, P(ótimo)=1.0.
- IBM: `execute_and_fetch:completed`.

## 2. Hipóteses

| ID | Hipótese | Classificação |
|---|---|---|
| H1 | Modelar interdependências reduz custo vs escolhas individuais | Confirmada no escopo experimental |
| H2 | QAOA ideal concentra probabilidade em ótimos melhor que amostragem uniforme no toy 2q | Parcialmente confirmada |
| H3 | Ruído deprecia a distribuição em relação ao ideal | Parcialmente confirmada |
| H4 | Execução física IBM é operacionalmente viável no toy 2q | Confirmada no exemplo de 2 qubits (1 job físico) |
| H5 | Há vantagem computacional quântica vs clássico exato | Não confirmada (instância minúscula; clássico exato trivial) |

## 3. Metodologia

- QUBO → Ising via `x=(I-Z)/2`, operador `SparsePauliOp`.
- Baseline clássico: enumeração exata, guloso individual, amostragem uniforme, enumeração factível one-hot.
- QAOA: `QAOAAnsatz`, COBYLA, múltiplos restarts/seeds, p∈{1,2,3}.
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

Status: completed. Detalhes em `simulator_results.json`.
Parâmetros exportados em `optimized_parameters.json`.

## 8. Resultados da simulação ruidosa

TVD (sintético vs ideal): 0.023193359375. Arquivo: `noisy_simulator_results.json`.
Não confundir com hardware real.

## 9. Resultados de hardware

Estado: execute_and_fetch:completed. IBM Kingston, 4.096 shots, 3.951 ótimos (96,46%). A execução física está concluída; sem demonstração de vantagem quântica.
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
- **KI-05**: resolvido — job IBM `dc3ibmdhdvas73bnvcfg` em `ibm_kingston` concluído (P(ótimo)≈0.965).
- **KI-06**: API key realocada de `experiments/` para `credentials/` (gitignored).
- Log completo: `docs/experiments/run_log_poc_v0.1.md` e `docs/experiments/ibm_qpu_run_poc_v0.1.md`.

## 14. Recomendações

1. Executar `--execute` apenas no toy 2q após revisar quota.
2. Ampliar benchmarks clássicos (MIP/CP-SAT) em v0.2.
3. Manter warm-start / Jev / ML para experimentos seguintes.

## 15. Conclusão

A etapa local da PoC v0.1 está concluída quando testes matemáticos, QAOA ideal, parâmetros persistidos e dry-run IBM passam.
A etapa física só conclui com recuperação de resultados de QPU.

## 16. Declaração de utilização de IA

Este código, experimentos e documentação da PoC v0.1 foram desenvolvidos com assistência de um agente de IA (Cursor) sob supervisão humana. Resultados numéricos foram gerados pelas bibliotecas instaladas e pelos scripts versionados; hipóteses não validadas permanecem explicitamente classificadas.
