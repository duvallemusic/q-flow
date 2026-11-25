# Prova Jev + Qiskit (PoC v0.1)

Gerado em 2026-11-25T21:57:11.742024+00:00 (rodada 20261125T214623Z).

Cenário sintético e ilustrativo. As probabilidades do Jev não foram calibradas com dados reais. Não demonstra vantagem quântica nem economia operacional real.

## 1. Jev (jev-latest, api.typesafe.ai)

| Rota | Risco de atraso (noul) | Condição (choice) | Dificuldade (score 0 a 3) | Tokens entrada/saída |
|---|---:|---|---:|---:|
| A | 0,86 | critica (confiança 0,77) | 2,11 | 768/96 |
| B | 0,11 | normal (confiança 0,97) | 0,00 | 729/95 |

Modelo pedido: `jev-latest`. Modelo que respondeu: `jev-1.14.0`.

## 2. Custos por rota: base + risco de atraso x multa de R$ 500,00

| Caminhão | Rota A | Rota B |
|---|---:|---:|
| 1 | R$ 300,00 + R$ 430,00 = R$ 730,00 | R$ 320,00 + R$ 55,00 = R$ 375,00 |
| 2 | R$ 290,00 + R$ 430,00 = R$ 720,00 | R$ 310,00 + R$ 55,00 = R$ 365,00 |

## 3. QUBO (x = 0 rota A, x = 1 rota B)

- Sem Jev (White Paper): `F = 660 - 50 x1 - 50 x2 + 70 x1x2`
- Com Jev: `F = 1520 - 425 x1 - 425 x2 + 70 x1x2`

| Estado | Significado | Sem Jev | Com Jev |
|---|---|---:|---:|
| 00 | caminhão 1 rota A, caminhão 2 rota A | R$ 660,00 | R$ 1.520,00 |
| 01 | caminhão 1 rota A, caminhão 2 rota B | R$ 610,00 | R$ 1.095,00 |
| 10 | caminhão 1 rota B, caminhão 2 rota A | R$ 610,00 | R$ 1.095,00 |
| 11 | caminhão 1 rota B, caminhão 2 rota B | R$ 630,00 | R$ 740,00 |

Ótimo sem Jev: 01, 10. Ótimo com Jev: 11. O sinal do Jev mudou a decisão.

## 4. QAOA no simulador ideal

Melhor configuração: p = 1, seed = 42. P(ótimo) = 97,12% em 4096 shots (amostragem uniforme: 24,39%).

## 5. IBM Quantum

Job dc3ljc5s2omc738dr9ig no backend ibm_fez: 3637 de 4096 shots no ótimo (88,79%). Contagens: {'11': 3637, '01': 218, '10': 204, '00': 37}.

Arquivos: jev_responses.json (request e resposta bruta do Jev, sem a chave), qubo_jev.json, simulator_results.json e, se rodou, ibm_*.json.
