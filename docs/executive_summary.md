# Executive Summary v2.0

Versão textual para manutenção; versão diagramada em `../releases/executive_summary_v2.0.pdf`.

## Página 1

Q-FLOW  /  EXECUTIVE SUMMARY
A logística é interdependente
Otimização híbrida de decisões, não apenas de distâncias.
01 / MERCADO E PROPOSTA DE VALOR
Q-FLOW  •  v2.0  /  QUANTUM PITCH 2026  /  25 NOV 2026
01
Q-Flow é uma proposta de plataforma B2B integrada a TMS e sistemas de telemetria, que combina
inteligência artificial estruturada, otimização matemática e aprendizado contínuo para coordenar
rotas, cargas, horários e abastecimento.
Problema
A rota mais curta nem sempre é a mais barata. Peso remanescente, relevo, combustível, clima, trânsito, prazos e
capacidade de docas afetam uns aos outros. Uma escolha localmente eficiente pode elevar o custo da operação
como um todo.
Topografia
Inclinação da via
Peso
Ordem de descarga
Velocidade
Trânsito e motor
Consumo previsto × preço do abastecimento
+ tempo, pedágio e risco de atraso
Mercado inicial e diferenciação
Transportadoras com rotas recorrentes e telemetria, operadores logísticos e fornecedores de TMS. A Q-Flow
complementa sistemas existentes por API. O diferencial proposto é integrar custos contextuais calibrados,
compilação de decisões, memória computacional e seleção adaptativa de solucionadores.
Modelo comercial
SaaS B2B
Implantação + assinatura por frota ou volume de
decisões.
Data Partnership
Créditos por históricos relevantes, autorizados e
governados.
CENÁRIO ECONÔMICO ILUSTRATIVO
R$ 36 mil/mês
100 veículos × R$ 12 mil/mês em combustível × 3% de redução hipotética. Economia bruta, não comprovada; exclui
custos do produto e implantação.

## Página 2

Q-FLOW  /  EXECUTIVE SUMMARY
Da realidade ao QUBO
A QPU atua em subproblemas combinatórios selecionados.
02 / VIABILIDADE TÉCNICA E CONCEITOS QUÂNTICOS
Q-FLOW  •  v2.0  /  QUANTUM PITCH 2026  /  25 NOV 2026
02
Histórico + telemetria + fontes externas
HIE: qualidade, contexto temporal e regras físicas
Jev + Adaptive Learning Engine
Choice / Score / Noul; calibração e previsão
Contextual Decision Compiler (CDC)
Grafo de dependências, candidatos, QUBO e Ising
Adaptive Solver Router (ASR)
Cache, similaridade, reprocessamento e warm-start
Memória / ML
Solução candidata
Clássico
OR-Tools / CPLEX
IBM Qiskit
QAOA / QPU
Validação → decisão operacional → feedback real
Restrições rígidas, qualidade, custo e atualização do ML
Formulação matemática e exemplo verificável
Escolhas binárias representam planos candidatos. Custos individuais e interações formam a função objetivo;
restrições são impostas por penalidades adequadas e validação explícita.
f(x₁,x₂) = 660 − 50x₁ − 50x₂ + 70x₁x₂
A + A
R$ 660
A + B
R$ 610
B + A
R$ 610
B + B
R$ 630
Exemplo de dois veículos: a concentração na rota A adiciona R$ 70. O ótimo de R$ 610 é verificado por
enumeração exata; não demonstra vantagem quântica. Com x = (1 − Z)/2, o Hamiltoniano é H = 627,5I + 7,5Z₁ +
7,5Z₂ + 17,5Z₁Z₂. QAOA busca soluções aproximadas com circuito parametrizado e otimizador clássico.
Escala: gerar planos e decompor conflitos classicamente; comparar QAOA em simulador e QPU com o mesmo
QUBO clássico. Validar viabilidade, gap, latência e custo total. Sem QPU disponível, o motor clássico mantém a
operação.

## Página 3

Q-FLOW  /  EXECUTIVE SUMMARY
Uma inteligência que acumula valor
Dados históricos reduzem o cold start; feedback valida as hipóteses.
03 / APRENDIZADO, VALIDAÇÃO E EXECUÇÃO
Q-FLOW  •  v2.0  /  QUANTUM PITCH 2026  /  25 NOV 2026
03
Aprendizado e memória computacional
Importar históricos anteriores à implantação, reconstruir apenas informações disponíveis à época e comparar
previsões com resultados observados. Modelos globais aprendem padrões compartilháveis; modelos privados
especializam por cliente. O histórico não é prova de causalidade nem elimina viés de seleção.
1. Histórico
ETL e auditoria
2. Calibração
Jev + ML
3. Decisão
QUBO + solver
4. Feedback
Telemetria real
Eficiência: cache exato versionado, recuperação por similaridade com revalidação, atualização de coeficientes
dependentes e warm-start QAOA experimental. O roteador seleciona o método por orçamento, qualidade e
disponibilidade.
Plano de validação
Modelagem
Distância × clássico multivariável
Custo, viabilidade e economia prevista
IA / ML
Sem Jev × Jev calibrado / ML
Brier score, erro de consumo, holdout
Quântico
Clássico × QAOA no mesmo QUBO
Gap, tempo, shots e custo total
Memória
Com × sem cache / warm-start
Reuso válido, latência e reprocessamento
MVP e governança
Começar com instâncias sintéticas reproduzíveis; validar simulador, integração Jev e ML; depois executar
shadow mode e piloto controlado com transportadora. Segregar tenants, minimizar dados pessoais, revisar
bases legais LGPD e contratos, controlar versões e auditar decisões.
ESTADO ATUAL  /  PROPOSTA CONCEITUAL
Verificação matemática do exemplo de dois bits e equivalência Ising. Ainda não demonstrados: QAOA em
hardware, integração Jev, ML com telemetria real, vantagem quântica, economia ou demanda comercial.
Referências centrais: IBM QAOA · Warm-starting quantum optimization · Solution caching · Calibração · Jev. Detalhamento no White
Paper v2.0. Uso de IA: ChatGPT apoiou pesquisa, estruturação, matemática, código, redação e diagramas; validação experimental
permanece pendente. Equipe a confirmar (2–6 integrantes).
