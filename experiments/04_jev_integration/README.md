# Experimento 04 — Integração Jev

Prova da camada Interpret: o Jev lê o contexto de cada rota e devolve três sinais tipados (Noul: risco de atraso; Choice: condição operacional; Score: dificuldade de acesso). O risco vira custo esperado (probabilidade x multa de atraso, padrão R$ 500) e entra nos termos lineares do QUBO de dois caminhões do White Paper. O QUBO é resolvido por enumeração e por QAOA no simulador ideal e, opcionalmente, no hardware da IBM.

Cenário sintético e ilustrativo. As probabilidades do Jev não foram calibradas com dados reais. Não demonstra vantagem quântica nem economia operacional real.

## Chaves (pasta `credentials/`, ignorada pelo git)

- `credentials/jev_apikey.json`: `{"apikey": "..."}`, criada em https://thejevai.com/settings/apikeys
- `credentials/ibm_apikey.json`: `{"apikey": "..."}`, criada no painel de https://quantum.cloud.ibm.com
- `credentials/ibm_crn.json`: `{"crn": "..."}`, opcional; sem ele a IBM escolhe a instância

A chave do Jev pode vir de dois lugares, e cada um só aceita a própria chave: o console oficial da TypeSafe (https://console.typesafe.ai/keys, padrão) ou o app thejevai.com (rode com `--jev-provider jevai`).

## Rodar

```bash
python scripts/run_jev_pipeline.py                  # Jev + QUBO + clássico + simulador
python scripts/run_jev_pipeline.py --reuse-jev      # refaz com as respostas salvas, sem gastar crédito
python scripts/run_jev_pipeline.py --ibm-dry-run    # confere conta, backend e circuito, sem enviar job
python scripts/run_jev_pipeline.py --ibm-execute    # envia 1 job (pede para digitar EXECUTE)
python scripts/run_jev_pipeline.py --ibm-job-id ID  # busca um job já enviado
```

Resultados em `results/jev_poc_v0.1/`: `REPORT.md`, `jev_responses.json` (request e resposta bruta do Jev, sem a chave), `qubo_jev.json`, `simulator_results.json` e `ibm_*.json`.

## Código

- `src/scoring/jev_client.py`: chamada à API (`POST https://thejevai.com/v1/systemone`), validação das respostas e novas tentativas em 429/529
- `src/scoring/jev_logistics.py`: perguntas, contexto das rotas e montagem do QUBO
- `src/credentials.py`: leitura das chaves locais
- `tests/test_jev_integration.py`: testes offline (Jev simulado e backend falso `FakeKingston`)

O `JevScoringProvider` de `src/scoring/providers.py` continua como placeholder; esta PoC usa `jev_logistics.py` direto.
