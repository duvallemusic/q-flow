# Prova Jev + Qiskit (PoC v0.2 - cenario real)

Gerado em 2026-11-26T00:23:03.119196+00:00 (rodada 20261126T002147Z).

Cenario montado com dados publicos rastreaveis em sources.json (OSRM, Open-Meteo, ANP e ANTT). Multa de atraso e custo de congestionamento sao parametros da equipe, nao medidos. As probabilidades do Jev nao foram calibradas com telemetria historica. Nao demonstra vantagem quantica.

## 1. Jev (jev-1.14.0, api.typesafe.ai)

| Rota | Risco de atraso (noul) | Condição (choice) | Dificuldade (score 0 a 3) | Tokens entrada/saída |
|---|---:|---|---:|---:|
| A | 0,33 | atencao (confiança 0,75) | 1,44 | 921/97 |
| B | 0,38 | atencao (confiança 0,75) | 1,47 | 922/97 |

Modelo pedido: `jev-1.14.0`. Modelo que respondeu: `jev-1.14.0`.

## 2. Custos por rota: base + risco de atraso x multa de R$ 500,00 (parametro da equipe, nao medido)

| Caminhão | Rota A | Rota B |
|---|---:|---:|
| 1 | R$ 438,79 + R$ 165,00 = R$ 603,79 | R$ 499,09 + R$ 190,00 = R$ 689,09 |
| 2 | R$ 484,18 + R$ 165,00 = R$ 649,18 | R$ 550,71 + R$ 190,00 = R$ 740,71 |

## 3. QUBO (x = 0 rota A, x = 1 rota B)

- Sem Jev (custos base ANTT): `F = 992.97 - 9.7 x1 - 3.47 x2 + 70 x1x2`
- Com Jev: `F = 1322.97 + 15.3 x1 + 21.53 x2 + 70 x1x2`

| Estado | Significado | Sem Jev | Com Jev |
|---|---|---:|---:|
| 00 | caminhão 1 rota A, caminhão 2 rota A | R$ 992,97 | R$ 1.322,97 |
| 01 | caminhão 1 rota A, caminhão 2 rota B | R$ 989,50 | R$ 1.344,50 |
| 10 | caminhão 1 rota B, caminhão 2 rota A | R$ 983,27 | R$ 1.338,27 |
| 11 | caminhão 1 rota B, caminhão 2 rota B | R$ 1.049,80 | R$ 1.429,80 |

Ótimo sem Jev: 10. Ótimo com Jev: 00. O sinal do Jev mudou a decisão.

## 4. QAOA no simulador ideal

Melhor configuração: p = 1, seed = 123. P(ótimo) = 95,92% em 4096 shots (amostragem uniforme: 26,12%).

## 5. IBM Quantum

Job dc3nnnuq4uuc73a7afng no backend ibm_fez: 3766 de 4096 shots no ótimo (91,94%). Contagens: {'00': 3766, '01': 130, '10': 156, '11': 44}.

Arquivos: sources.json, jev_responses.json (request e resposta bruta do Jev, sem a chave), qubo_jev.json, simulator_results.json e, se rodou, ibm_*.json.
