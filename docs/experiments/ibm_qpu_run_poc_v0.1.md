# Execução IBM QPU — PoC v0.1

## Credenciais

- Arquivos recebidos em `experiments/02_qaoa_simulator/` foram **realocados** para `credentials/` (gitignored).
- `credentials/ibm_apikey.json` usado para `QiskitRuntimeService.save_account(channel='ibm_quantum_platform')`.
- `credentials/ibm_crn.json` estava **vazio**; a instância `open-instance` (plano open) foi selecionada automaticamente.
- Nenhum token foi commitado. `.gitignore` reforçado para `**/apikey.json`, `**/crn.json`, `credentials/`.

## Job físico

| Campo | Valor |
|---|---|
| Job ID | `dc3ibmdhdvas73bnvcfg` |
| Backend | `ibm_kingston` |
| Shots | 4096 |
| p | 2 |
| Instância lógica | two_truck_whitepaper (2 qubits) |
| Status final | DONE / completed |
| P(ótimo) | 0.9646 |
| Estado mais frequente | `10` (ótimo) |
| TVD vs ideal local | 0.0354 |
| Profundidade lógica | 2 |
| Profundidade transpilada | 30 |

## Interpretação

- A execução física **não** foi inventada; resultado recuperado do job IBM.
- P(ótimo) na QPU (~96,5%) ficou próxima do simulador ideal (100% na melhor configuração local).
- Isso **não** constitui vantagem quântica computacional; o toy é minúsculo e o clássico exato é trivial.
- Tempo de fila/execução remota não deve ser comparado diretamente ao runtime clássico local.

## Artefatos

- `results/quantum_poc_v0.1/ibm_quantum_results.json`
- `results/quantum_poc_v0.1/ibm_job_submitted.json` (layout truncado)
- `results/quantum_poc_v0.1/charts/hardware_distribution.png`

## Segurança

Recomenda-se rotacionar a API key se ela tiver sido compartilhada fora do cofre local, pois transitou por um arquivo temporário na pasta de experimentos antes da realocação.
