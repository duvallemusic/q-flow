# Q-Flow — Adaptive Logistics Intelligence

Proposta de startup B2B para o Qiskit Fall Fest 2026 (IBM + FIAP). Integra dados históricos, Jev, machine learning, otimização clássica e Qiskit.

**Estado:** conceitual. Exemplo de dois bits verificável por enumeração; QAOA, Jev, ML e piloto ainda não validados. Sem alegação de vantagem quântica.

## Documentação
- [White Paper v2.0 (PDF)](releases/whitepaper_v2.0.pdf)
- [Executive Summary v2.0 (PDF)](releases/executive_summary_v2.0.pdf)
- [Texto do White Paper](docs/whitepaper.md) e [resumo](docs/executive_summary.md)
- [Arquitetura](docs/architecture/overview.md) e [referências](docs/references.md)
- [Materiais iniciais do Challenge](docs/challenge/) (versão anterior, para referência; o White Paper v2.0 é a fonte de verdade)

## Reproduzir a verificação clássica
```bash
python3 experiments/01_qubo_classical/demo_qubo.py
python3 -m unittest discover -s tests
```

## Experimentos planejados
Simulador QAOA, hardware IBM, Jev, calibração ML e benchmark integrado. Cada execução deve registrar versão, dados, seed, métricas e limitações.

## Governança
Não commitar telemetria de clientes, chaves, arquivos .env ou dados pessoais. Acesso privado recomendado. Nome e equipe a confirmar; licença não definida.

## Transparência
ChatGPT foi usado como apoio à pesquisa, modelagem, código, redação e diagramas. Resultados não validados são identificados nos documentos.
