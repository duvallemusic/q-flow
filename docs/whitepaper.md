# Q-Flow — White Paper v2.0

Versão textual extraída do PDF publicado; diagramas e formatação de referência estão no PDF em `releases/whitepaper_v2.0.pdf`. Para alterações futuras, revisar esta transcrição e atualizar a versão.


## Página 01


PROPOSTA CONCEITUAL  /  NOVEMBRO 2026
WHITE PAPER  /  PROPOSTA DE STARTUP
Q-FLOW
Inteligência logística adaptativa
Otimização híbrida quântica-clássica
Decisões interdependentes, IA estruturada,
machine learning e memória computacional
para operações logísticas de alta complexidade.
COLLECT. INTERPRET. OPTIMIZE. LEARN. REPEAT.
Qiskit Fall Fest 2026  |  Quantum Pitch
IBM Quantum + FIAP  |  25 de novembro de 2026
Versão 2.0  |  Proposta conceitual e plano de validação
Equipe: identificação a confirmar no formulário oficial (2 a 6 integrantes).


## Página 02


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
02
Q-FLOW / RESUMO EXECUTIVO
Uma infraestrutura de decisões
Tese de produto, mercado e pesquisa aplicada em uma única arquitetura.
A Q-Flow propõe uma plataforma B2B de otimização logística integrada aos sistemas de transporte já
utilizados pelas empresas. O problema central não é simplesmente encontrar a menor distância: é decidir
conjuntamente rotas, veículos, sequência de entregas, abastecimento e horários quando cada escolha
altera os custos das demais. Peso, inclinação, clima, preço de combustível e prazos têm efeitos distintos
conforme o contexto.
O produto combina quatro paradigmas: processamento determinístico para medir custos e restrições; Jev,
da TypeSafe AI, para interpretar informações qualitativas em respostas estruturadas; machine learning
supervisionado para calibrar previsões com resultados observados; e Qiskit para estudar subproblemas de
otimização combinatória representados por QUBO e Hamiltonianos de Ising. O sistema mantém uma
alternativa clássica, sem depender de disponibilidade de QPU para operar.
Collect
Histórico + eventos
Interpret
Jev + ML
Optimize
Clássico + Qiskit
Learn
Feedback real
Figura 1. Fluxo central de geração de valor; o aprendizado realimenta as próximas decisões.
Produto e modelo comercial
A entrada comercial é uma API de otimização para transportadoras, operadores logísticos e fornecedores
de TMS. A receita proposta combina implantação, assinatura e faixas de uso. O programa Data Partnership
reduz custos de implantação em troca de acesso autorizado a históricos de qualidade, com finalidade
delimitada e isolamento entre clientes. Modelos globais aprendem apenas padrões compartilháveis;
modelos privados preservam especificidades de cada operação.
Hipótese e estágio de maturidade
A hipótese é que uma melhor modelagem de custos, combinada com recuperação de soluções e
aprendizado histórico, reduza custos operacionais e computacionais. O valor específico da QPU será
investigado contra referências clássicas equivalentes. O projeto encontra-se em fase conceitual: existe um
exemplo QUBO de dois bits verificável por enumeração, mas não há piloto com transportadora, calibração
de Jev em logística ou demonstração de vantagem quântica.
Proposta de valor
Transformar dados históricos e contexto operacional em decisões validadas, com aprendizado contínuo e
uso seletivo de computação quântica.


## Página 03


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
03
Q-FLOW / GUIA DE LEITURA
Estrutura e critérios da banca
O documento é autossuficiente: aprofunda a proposta sem exigir uma demonstração ao vivo.
Pág.
Tema
Critério atendido
04–05
Problema, mercado e trabalhos relacionados
Mercado / viabilidade
06–08
Dependências, QUBO, Ising e QAOA
Conceitos quânticos
09–10
Jev e compilador contextual
Viabilidade / conceitos
11–13
ML, memória, warm-start e seleção de solver
Viabilidade / conceitos
14–16
Histórico, parceria e governança
Mercado / viabilidade
17–18
Arquitetura e integração do produto
Viabilidade
19
Modelo de negócio e cenários econômicos
Mercado
20–21
Experimentos, MVP e roadmap
Viabilidade / conceitos
22–23
Riscos, referências e declaração de IA
Todos
Regras consideradas
A apresentação de abertura do Qiskit Fall Fest 2026 estabelece a criação de uma ideia de startup que use
computação quântica, sem programação obrigatória. A avaliação considera mercado, viabilidade técnica e
uso dos conceitos. O material exigido é apresentação, descrição e pitch; vídeo de até três minutos vale
ponto extra. A equipe deve ter de dois a seis integrantes e o uso de IA precisa ser declarado. Prazo
informado: 25/11/2026 às 23h45. Fonte [1].
Convenção de evidência
Classificação
Significado
Fundamento estabelecido
Método ou conceito com referência técnica/científica.
Proposta Q-Flow
Decisão de arquitetura ou hipótese comercial, ainda não implementada ou validada
integralmente.
Exemplo ilustrativo
Números fictícios para demonstrar a lógica; não constituem previsão de economia.
Verificação matemática
Resultado calculável de maneira exata no exemplo de dois bits.
A composição da equipe e os campos finais de submissão devem ser confirmados pela equipe no formulário
oficial. Não há alegação de parceria, aprovação, cliente, receita, propriedade intelectual registrada ou
execução em hardware IBM.


## Página 04


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
04
Q-FLOW / 01 / MERCADO
O custo invisível da distância
Rotas individualmente eficientes podem produzir operações globalmente ineficientes.
A roteirização convencional resolve problemas relevantes de distância e tempo, mas o custo efetivo de um
transporte depende de outros fatores: massa total, sequência de descarga, velocidade, perfil altimétrico,
paradas, pedágios, preço de abastecimento, janela de entrega e disponibilidade de recursos compartilhados.
O problema de roteirização com emissões e consumo (Pollution Routing Problem) modela parte dessas
relações [2].
Topografia
Inclinação e altitude
Peso remanescente
Ordem de descarga
Velocidade
Trânsito e regime
Consumo previsto
Modelo físico + correção estatística
Preço diesel
Posto e instante
Custo energético
Litros × preço
Prazo e risco
Penalidade esperada
Custo total esperado
Combustível, tempo, risco, pedágio
Figura 2. Exemplo de propagação de dependências. A relação não pressupõe causalidade estimada pelo Jev.
Público inicial e problema a validar
O cliente ideal inicial é uma transportadora com rotas recorrentes, telemetria acessível, despesas
relevantes de combustível e capacidade de comparar recomendações com sua política atual. A operação de
serra é um caso de uso particularmente didático: duas rotas de distâncias semelhantes podem demandar
esforços energéticos diferentes. O produto precisa mostrar valor incremental frente ao TMS existente, não
apenas frente a uma escolha ingênua por distância.
Questão de pesquisa
Quanto do ganho decorre de representar melhor os custos? Quanto decorre do ML? E em quais
instâncias um algoritmo quântico se torna competitivo?


## Página 05


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
05
Q-FLOW / 02 / FUNDAMENTAÇÃO
Trabalhos relacionados e posição
A inovação proposta está na integração, não na reinvenção de técnicas estabelecidas.
Linha existente
O que oferece
Papel na Q-Flow
VRP / PRP [2]
Rotas sob restrições; custo de
combustível e emissões.
Modelo de domínio e referência clássica.
QAOA [3,4]
Algoritmo variacional para problemas
discretos.
Subproblemas QUBO pequenos e
benchmarks.
Warm-start [5]
Inicialização a partir de relaxação
clássica.
Investigação de reutilização de soluções.
Predict-and-optimize [6]
Aprender parâmetros úteis a uma
otimização; cache no treinamento.
Inspirar ML, recuperação e avaliação por
custo de decisão.
Jev [7]
Respostas tipadas Choice, Score e
Noul.
Transformar contexto qualitativo em sinais
estruturados.
PTV Routing [8]
Roteirização comercial com restrições
e custos.
Concorrente e referência de funcionalidades.
O que não é original por si só
Roteirização multicritério, otimização quadrática binária, cache, aprendizado supervisionado, QAOA e
integração por APIs são técnicas existentes. Uma empresa estabelecida já pode combinar múltiplos custos
e restrições em um roteirizador comercial. A diferenciação, se comprovada, está na compilação contextual,
no reaproveitamento computacional governado por dependências e na aprendizagem histórica com
feedback, integrados a um roteador adaptativo de solucionadores.
Concorrência e alternativas
O concorrente prático é o conjunto de ferramentas e processos já adotado pelo cliente: TMS, planejadores,
regras de negócio, serviços de roteirização e otimizadores matemáticos. OR-Tools e CPLEX são referências
de solução clássica, não substitutos automaticamente equivalentes a um produto SaaS. A Q-Flow deve
avaliar se adicionar uma camada de inteligência produz valor incremental suficiente para justificar
implantação e manutenção.
Posicionamento
Optimization as a Service: componente interoperável, não substituto obrigatório do TMS. Nenhuma
alegação de exclusividade ou patenteabilidade sem pesquisa de anterioridade.


## Página 06


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
06
Q-FLOW / 03 / MODELAGEM
Variáveis e dependências
Separar medidas contínuas de decisões binárias evita desperdício de qubits e erros de
modelagem.
Tipo
Exemplo
Como tratar
Medida contínua
Massa, inclinação, preço, velocidade.
Modelos clássicos; manter unidades e incerteza.
Decisão binária
Selecionar plano A, veículo B ou
horário C.
Variável x   {0,1} no QUBO.
Interação
Dois planos disputam uma doca.
Coeficiente quadrático de custo adicional.
Estado dependente
Carga restante após cada entrega.
Simulação por plano ou variáveis auxiliares.
Restrição rígida
Limite de peso, jornada,
compatibilidade.
Filtrar alternativas e validar solução.
Exemplo de custo físico por trecho
Uma estimativa de energia de tração considera resistência ao rolamento, inclinação, arrasto aerodinâmico e
aceleração. Seja m a massa, v a velocidade, θ a inclinação, d a distância e η a eficiência; uma primeira
aproximação para energia é:
E ≈ d · max(0, m g Crr cos θ + m g sin θ + ½ ρ Cd A v² + m a) / η
O modelo deve incluir marcha lenta, frenagem, perfil do motor, eficiência variável e consumo de acessórios
quando relevantes. O termo max é uma simplificação para não inferir energia negativa de combustível;
regeneração e descidas exigem tratamento específico. Calibrar litros previstos com telemetria, respeitando
unidades e incerteza. O preço do diesel é aplicado ao volume e local efetivo de abastecimento, não a cada
município atravessado.
Modelo de objetivos
J = Ccomb + Cped + Ctempo + Cpenalidade + Cexterno
Custos monetários podem ser somados diretamente se não houver dupla contagem. Para múltiplos
objetivos com unidades distintas, normalizar e declarar os pesos ou apresentar fronteira de Pareto.
Segurança, limites legais e capacidade não são objetivos negociáveis.


## Página 07


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
07
Q-FLOW / 04 / QUBO
Compilar escolhas interdependentes
De planos logísticos viáveis a uma função quadrática binária.
A Q-Flow propõe gerar classicamente um conjunto reduzido de planos candidatos por veículo. Um plano já
inclui sequência, carga remanescente, horários estimados, consumo e abastecimento. A variável xvk
representa a escolha do plano k do veículo v. Cada conjunto deve respeitar exatamente uma escolha;
quando a formulação cobre pedidos, cada entrega deve ser atendida uma vez. Interações representam
conflitos ou benefícios conjuntos.
F(x) = Σᵢ cᵢ xᵢ + Σi<j qij xi xj + λ Σv (Σk xvk − 1)²
cᵢ é o custo previsto de um plano, qᵢ  é o impacto incremental de escolher i e j simultaneamente, e λ
penaliza a seleção incorreta. Interações positivas representam congestionamento ou competição por
capacidade; negativas podem representar sinergias, se justificadas. Restrições adicionais, como cobertura
de pedidos, podem ser incorporadas por penalidades ou tratadas na geração e validação de candidatos.
Exemplo verificável: dois veículos e duas rotas
Defina x₁ = 0 para A e 1 para B no caminhão 1; o mesmo para x₂ no caminhão 2. A custa R$ 300 e R$ 290;
B custa R$ 320 e R$ 310. Se ambos selecionam A, acrescenta-se R$ 70 de congestionamento. Uma variável
por veículo já garante uma das duas rotas.
F = 300 + 20x₁ + 290 + 20x₂ + 70(1−x₁)(1−x₂)
F = 660 − 50x₁ − 50x₂ + 70x₁x₂
x₁x₂
Escolhas
Custo total
00
A + A
R$ 660
01
A + B
R$ 610
10
B + A
R$ 610
11
B + B
R$ 630
Resultado matemático
A enumeração confirma dois ótimos de R$ 610, contra R$ 660 da escolha individual. A diferença de R$
50 (7,58%) é fictícia e decorre da modelagem da interação, não de uma vantagem quântica.


## Página 08


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
08
Q-FLOW / 05 / COMPUTAÇÃO QUÂNTICA
Do QUBO ao Hamiltoniano
A função objetivo torna-se uma energia cujos estados de menor valor codificam boas
decisões.
Em um computador quântico de portas, a substituição xᵢ = (1 − Zᵢ)/2 converte a função binária em um
Hamiltoniano diagonal na base computacional. O operador de Pauli Z possui autovalores +1 para |0⟩ e −1
para |1⟩. Para o exemplo anterior, a expansão produz:
H = 627,5 I + 7,5 Z₁ + 7,5 Z₂ + 17,5 Z₁Z₂
As energias dos estados |00⟩, |01⟩, |10⟩, |11⟩ reproduzem R$ 660, R$ 610, R$ 610 e R$ 630. O termo
constante pode ser omitido do circuito, mas deve ser restituído no relatório de custo. A equivalência é
exata para este exemplo.
QAOA: ciclo híbrido [3,4]
Hamiltoniano H
Coeficientes QUBO
Circuito QAOA
Estado + camadas p
Amostragem
Bitstrings e energia
Otimizador clássico
Atualiza β e γ
Validação
Custo e restrições
Figura 3. QAOA alterna evolução de custo e mistura; parâmetros são ajustados classicamente.
|ψ(γ,β)⟩ = ∏l=1…p exp(−iβl HM) exp(−iγl H) |+⟩ⁿ
Com p camadas, um otimizador clássico escolhe parâmetros γ e β para reduzir a energia esperada.
Medições geram candidatos binários; a aplicação calcula o custo real e descarta soluções inválidas. Mais
camadas não garantem melhor resultado em hardware ruidoso. O benchmark registra profundidade, portas
de dois qubits, shots, número de avaliações e latência total.
Limite científico
A computação quântica não avalia todas as soluções e retorna automaticamente a melhor. QAOA é
aproximado e variacional; vantagem prática não foi demonstrada para a Q-Flow.


## Página 09


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
09
Q-FLOW / 06 / JEV
Inteligência contextual estruturada
A IA interpreta sinais qualitativos; o compilador converte resultados em parâmetros
economicamente coerentes.
O Jev é apresentado como modelo de decisões tipadas, com três primitivas documentadas [7]. Seu papel
não é calcular física, escolher a solução final ou estabelecer restrições legais, mas extrair sinais de
relatórios, descrições operacionais e contexto estruturado. A API deve ser acessada por adaptador
substituível, com timeouts, controle de versão e fallback.
Primitivo
Questão logística
Saída normalizada (ilustrativa)
Choice
Qual a condição operacional descrita?
normal / atenção / crítica
Score
Qual a dificuldade de acesso, segundo escala descrita?
0,75 após normalização
Noul
Há evidência contextual de risco de atraso?
0,80 como sinal do modelo
Contrato de avaliação
Entrada: snapshot anterior à decisão contendo dados permitidos, por exemplo descrição de obras, previsão
de chuva, tipo de veículo, classe de carga e janela contratual. Cada pergunta tem critérios explícitos,
unidade ou legenda, versão e identificador. Saída interna: valor, confiança quando disponível,
contexto_hash, modelo, horário, evidência de origem e status de validade. O formato é uma interface
nossa, não uma promessa sobre o JSON nativo do fornecedor.
Converter sinal em custo esperado
Crisco = Pcalibrada(atraso | contexto, plano) × impacto financeiro
Exemplo: rota A custa R$ 300 e tem risco calibrado de 20%; rota B custa R$ 320 e tem risco de 4%. Com
penalidade fixa de R$ 500, os custos esperados são R$ 400 e R$ 340. A rota B é preferível nesse cenário.
Se não houver calibração, o score deve ser tratado como sinal ordinal ou estimativa incerta, não como
frequência empírica.
Salvaguardas
Não enviar dados pessoais desnecessários, não assumir precisão em português sem avaliação, não
extrapolar latência/preço de divulgação para produção, e nunca permitir que IA substitua restrições de
segurança.


## Página 10


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
10
Q-FLOW / 07 / CDC
Contextual Decision Compiler
O núcleo de transformação de contexto real em problemas matemáticos auditáveis.
Snapshot operacional
Dados versionados e disponibilidade temporal
Grafo de dependências
Relações físicas, econômicas e contextuais
Candidatos e coeficientes
Custos individuais + interações incrementais
QUBO / Ising
Restrições, penalidades e mapeamento de bits
Problem manifest
IDs, escalas, versão e trilha de auditoria
Figura 4. Compilação proposta; cada coeficiente preserva sua origem e unidade.
Contrato e regras de compilação
O CDC recebe planos candidatos, custos calculados, previsões calibradas e regras rígidas. Para cada termo,
registra origem, unidade, dependências, timestamp e versão. Interações devem corresponder a um efeito
marginal: qᵢ  = C(i,j) − C(i,0) − C(0,j) + C(0,0), sob um contexto definido. Evitar aplicar simultaneamente um
custo individual de atraso e a mesma penalidade como interação.
Para restrições exatamente-uma, elevar a soma dos bits ao quadrado gera termos lineares e pares. Escolher
λ por limite de melhoria possível ao violar a restrição ou por teste sistemático; penalidades excessivas
podem piorar a escala numérica e a resolução da energia. Restrições críticas são verificadas
independentemente após a solução. Interações de ordem superior só devem ser reduzidas a QUBO com
variáveis auxiliares se o custo em qubits for aceitável.
Artefato de saída
Um manifest imutável contém problem_id, tenant_id, feature_version, candidates, linear_terms,
quadratic_terms, constraints, normalization, mapping e provenance. A função objetivo deve ser
reproduzível sem chamar o Jev novamente. Uma matriz esparsa preserva somente interações justificadas.


## Página 11


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
11
Q-FLOW / 08 / ADAPTIVE LEARNING
Aprender com a operação real
Machine learning corrige previsões; o motor de otimização continua decidindo sobre
alternativas.
O Adaptive Learning Engine (ALE) aprende com combustível observado, atrasos, tempos e custos
realizados. Inicialmente, utilizar modelos físicos como baseline e regressão logística para riscos; comparar
com gradient boosting (XGBoost/LightGBM) e correção de resíduos para consumo. O Jev pode ser uma
feature, mas seu valor incremental deve ser testado.
ŷconsumo = ymodelo_físico + gθ(X) | pcal = fθ(pJev, X)
Calibração e critérios de confiança
Separar treino, calibração e teste por tempo, viagem e, quando possível, por cliente. Avaliar MAE/RMSE de
consumo, Brier Score e diagramas de confiabilidade para risco. Usar calibração sigmoidal ou isotônica
conforme volume e validação [9]. Monitorar erros por tipo de frota, região, estação e condições raras;
médias agregadas podem ocultar falhas relevantes.
Grupo hipotético
Jev
Frequência observada
Ajuste a investigar
Serra, carga pesada
80%
62%
Superestimação
Rodovia plana, chuva
45%
22%
Superestimação
Obras / restrições
50%
71%
Subestimação
Tabela ilustrativa: nenhum desses valores foi medido. Avaliar intervalos e tamanho de amostra antes de ajustar.
Ciclo de treinamento e publicação
Observar
Telemetria
Treinar
Modelo candidato
Validar
Holdout temporal
Publicar
Registro / rollback
Figura 5. Treinamento fora do fluxo crítico e promoção controlada de versões.
Registrar dados, código, parâmetros, métricas e distribuição de features com MLflow ou equivalente. Em
produção, detectar drift e dados fora de distribuição, usar fallback e alertar a equipe quando necessário.
Retreinar em lotes inicialmente; aprendizado online só após demonstrar estabilidade. Não promover
modelos apenas porque o erro de treino caiu.


## Página 12


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
12
Q-FLOW / 09 / MEMÓRIA COMPUTACIONAL
Não recalcular o que já sabemos
Reutilização determinística, recuperação aproximada e atualização incremental têm garantias
diferentes.
Mecanismo
O que reutiliza
Condição de segurança
Cache exato
Cálculo de trecho, avaliação, QUBO ou
solução.
Mesmas entradas, versão, escopo e
validade.
Similaridade
Solução candidata de problema próximo.
Recalcular custo e validar todas as
restrições.
Computação incremental
Coeficientes não afetados por um evento.
Propagação completa das dependências.
Warm-start
Solução ou parâmetros promissores.
Nova otimização e benchmark
independente.
Topografia
Sem mudança
Peso
Sem mudança
Preço diesel
Alterado
Consumo estimado
Reutilizado
Preço atualizado
Nova versão
Coeficientes do QUBO
Recalcular custos afetados
Figura 6. Exemplo de atualização por dependência. A solução global ainda pode mudar.
Implementação
Usar hashes canônicos com versões de dados, modelos, restrições, escopo do cliente e janela temporal;
Redis como cache rápido e PostgreSQL para artefatos persistentes. Um índice vetorial ou distância
ponderada em features normalizadas pode recuperar top-k candidatos; a similaridade não autoriza
execução automática. Reavaliar custo, disponibilidade, capacidade e segurança, e comparar com um
baseline ou limite de qualidade.
A literatura de cache de soluções em predict-and-optimize demonstra aplicação no treinamento [6];
transportar a ideia para inferência operacional é uma hipótese própria. Medir taxa de reutilização válida,
tempo economizado e regret de qualidade, não apenas hit rate.


## Página 13


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
13
Q-FLOW / 10 / ASR
Otimizar o próprio processamento
Um seletor adaptativo decide quando reaproveitar, resolver classicamente ou experimentar
Qiskit.
Solicitação de decisão
Snapshot + prazo de resposta
Cache exato válido?
Sim: recuperar e validar; não: seguir
Candidato semelhante?
Validar, reparar ou usar como warm-start
Subproblema adequado à QPU?
Limites de bits, conectividade, orçamento e prazo
Comparar e escolher
Clássico / QAOA / solução reaproveitada
Figura 7. Adaptive Solver Router (ASR), com fallback clássico e orçamento de execução.
Warm-start QAOA
O método de Egger, Mareček e Woerner inicializa o estado a partir da solução de uma relaxação clássica
[5]. O Qiskit oferece tutoriais de warm-start [10]. A Q-Flow pode usar histórico para recuperar soluções,
inicializar uma relaxação ou sugerir parâmetros variacionais; reaproveitar um bitstring não equivale
automaticamente ao método formal de warm-start. Comparar inicializações aleatórias, clássicas e
informadas, com mesmos recursos e seeds.
Política inicial de roteamento
Começar com regras determinísticas: cache válido tem prioridade; referência clássica responde dentro do
SLA; QAOA roda em modo experimental para instâncias elegíveis, sem bloquear a decisão. Quando houver
histórico suficiente, treinar um seletor para prever custo de execução, probabilidade de viabilidade e gap
em relação a referência. O objetivo é minimizar custo computacional sob limites de qualidade e latência, e
não maximizar chamadas quânticas.
Exemplo de métrica
Em 10 mil solicitações fictícias, se 3 mil forem recuperadas exatamente, 2.800 por similaridade validada e
2.100 por processamento parcial, restam 2.100 completas (79% menos chamadas completas). Isso não
implica 79% de economia financeira.


## Página 14


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
14
Q-FLOW / 11 / HIE
Aprender antes de implantar
A Historical Intelligence Engine reduz cold start usando histórico de telemetria autorizado.
Ingestão histórica
TMS, ERP, GPS, CAN, CSV ou API
Qualidade e reconstrução
Normalizar, map-match, enriquecer por data
Replay de contexto
Jev recebe apenas informação pré-decisão
Treino e calibração
Comparar com desfecho efetivamente observado
Backtesting / shadow mode
Avaliar recomendações antes do piloto
Figura 8. Onboarding de dados históricos: o resultado real é rótulo, nunca feature antecipada.
Pipeline de aquisição
Solicitar catálogo de fontes, dicionário, cobertura temporal e amostras antes de precificar a integração.
Ingerir em zona bruta segregada; deduplicar, padronizar unidades e fusos, identificar gaps, conciliar
abastecimentos e mapear GPS à malha. Cada viagem recebe identificador, instante de decisão, features
disponíveis naquele momento e observações posteriores. Enriquecer topografia com DEM [11] e preços
históricos ANP [12], respeitando licenças e granularidade.
Risco de viés e contrafactual
Mais registros não garantem representatividade. Milhões de viagens em uma única rota podem ter menos
valor generalista que um conjunto menor com diversidade de veículos, clima e relevo. Histórico mostra o
resultado das ações escolhidas, não das alternativas rejeitadas. Técnicas off-policy exigem cobertura e
premissas fortes [13]. Usar simulação de alternativas como estimativa, não como observação real; só um
piloto controlado pode comprovar economia realizada.


## Página 15


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
15
Q-FLOW / 12 / DATA PARTNERSHIP
Dados como contrapartida econômica
Um modelo de aquisição de conhecimento que também reduz a barreira de adoção.
A Q-Flow propõe descontos de implantação ou créditos temporários em troca de contribuição histórica
autorizada, útil e contratualmente delimitada. O cliente pode contratar sem contribuir para o modelo
global. O benefício comercial deve refletir custo de integração e valor marginal da base, não volume bruto.
A proposta permite pré-treinar modelos antes de iniciar a operação.
Parceiro A
Telemetria de serra
Parceiro B
Distribuição urbana
Parceiro C
Carga refrigerada
Governança e tratamento
Somente sinais autorizados e compartilháveis
Modelo global
Padrões físicos e operacionais
Modelo privado A
Especialização
Modelo privado B
Especialização
Modelo privado C
Especialização
Figura 9. Modelos globais e privados; dados comerciais brutos não são compartilhados entre tenants.
Data Contribution Score (hipótese inicial)
Critério
Peso
Como avaliar
Qualidade + completude
45%
Consistência, rótulos, cobertura e unidades
Diversidade + novidade
40%
Cenários novos e lacunas do modelo
Volume útil + atualização
15%
Viagens independentes, recência e continuidade
Exemplo de ponderação: 25% qualidade, 20% completude, 20% diversidade, 20% novidade, 10% volume e
5% atualização. Validar sensibilidade dos pesos e o ganho marginal em holdout antes de definir desconto. O
data flywheel é um objetivo, não uma garantia de efeito de rede.


## Página 16


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
16
Q-FLOW / 13 / GOVERNANÇA
Privacidade e confidencialidade
A aquisição de dados deve ser comercialmente aceitável e juridicamente sustentável.
Dados de GPS, jornada e telemetria podem identificar motoristas direta ou indiretamente. A LGPD [14]
exige avaliar finalidade, necessidade, base legal, transparência, segurança e direitos dos titulares. A
autorização empresarial não basta para legitimar todo tratamento de dados pessoais; a pseudonimização
não é sinônimo de anonimização. Definir responsabilidades de controlador/operador conforme cada
finalidade e obter revisão jurídica antes do piloto.
Categoria
Uso privado
Uso global
Características físicas do veículo
Permitido conforme contrato
Somente atributos necessários e
autorizados
Consumo agregado e efeitos de
relevo
Sim
Possível após avaliação de risco
GPS detalhado, motorista,
identificadores
Somente quando indispensável
Não por padrão
Contratos, margens, clientes e tarifas
Isolado por tenant
Não
Rotas estratégicas
Isoladas por tenant
Não, salvo derivação segura autorizada
Controles desde o desenho
Separar tenants por política de acesso, chaves e escopos de armazenamento; criptografar trânsito e
repouso; registrar acessos, alterações e exportações; aplicar retenção e descarte, revisão de permissões e
resposta a incidentes. Remover identificadores antes de chamadas externas. Avaliar transferência
internacional, subprocessadores e termos de retenção/treinamento de Jev e IBM; enviar à QPU apenas
coeficientes e mapeamento abstrato, evitando informações comerciais ou pessoais desnecessárias.
Condições contratuais do programa
O contrato deve especificar finalidade privada e global, direitos sobre dados e modelos derivados, prazo,
autorização de uso, auditoria, encerramento, devolução/eliminação e tratamento de modelos já treinados.
Modelos globais podem revelar informação por ataques de inferência; avaliar risco e limitar exportação.
Federated learning pode ser estudado depois, mas não elimina riscos por si só.
Regra comercial
Oferecer Q-Flow Private sem compartilhamento global; Partner com contribuição voluntária e
governada; Founding Partner com histórico e participação em pilotos. Descontos não são condicionantes
de direitos legais.


## Página 17


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
17
Q-FLOW / 14 / ARQUITETURA
Arquitetura consolidada
Uma camada de aprendizado retroalimenta a representação matemática, a memória e o
seletor de algoritmos.
Histórico / Data Partnership
HIE: importação e qualidade
Telemetria e APIs
Eventos e contexto atual
Processamento determinístico
Modelos físicos, regras rígidas, custos
Jev + Adaptive Learning Engine
Contexto estruturado, calibração, previsão
Contextual Decision Compiler
Grafo, candidatos, QUBO e Ising
Adaptive Solver Router
Cache, similaridade, limites e warm-start
Memória / ML
Recuperação
Clássico
OR-Tools / CPLEX
IBM Qiskit
QAOA / QPU
Validation & Benchmark
Custos, restrições e comparação
Execução logística
API / TMS / aprovação operacional
Real-world Feedback
Telemetria, rótulos e métricas
Figura 10. Arquitetura lógica proposta. O ciclo de feedback (tracejado) alimenta treinamento e atualização de artefatos; toda
decisão passa pela validação.
A execução não depende exclusivamente de Jev ou QPU: adaptadores independentes, regras
determinísticas e fallback clássico preservam disponibilidade. O CDC e o ASR são os pontos de integração e
auditoria.


## Página 18


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
18
Q-FLOW / 15 / ENGENHARIA
Integração e desenho de software
A primeira versão pode ser um monólito modular, com workers separados para tarefas de
alto custo.
Camada
Tecnologia sugerida
Responsabilidade
API e UI
FastAPI, React/Next.js
Integração TMS, revisão e explicação de decisões
Dados
Postgres, PostGIS, objetos
Histórico, snapshots, features, proveniência
Rotas
OSRM + fonte de restrições
Candidatos e tempos; perfil validado para caminhões
Contexto
Adaptador Jev
Questões tipadas, cache, timeout
ML
scikit-learn, XGBoost, MLflow
Treino, calibração e registro
CDC
Python, NumPy, NetworkX
Grafo e compilação QUBO
Solvers
OR-Tools/CPLEX; Qiskit
Clássico, simulação e QPU experimental
Memória
Redis, pgvector opcional
Cache versionado e busca aproximada
Contrato de API (proposto)
POST /v1/optimization-jobs recebe snapshot_id, vehicle_ids, order_ids, objetivos e prazo. Retorna job_id e
status. GET /v1/optimization-jobs/{id} retorna plano, custo estimado, restrições verificadas, solver, versão
e qualidade. POST /v1/outcomes vincula eventos reais a decision_id. POST /v1/historical-imports inicia
ingestão privada com manifesto de autorização.
Entidades persistentes
tenant, consent_or_authorization_scope, vehicle, trip, segment, order, telemetry_event, snapshot,
feature_set, contextual_assessment, candidate_plan, problem_manifest, solver_run, decision,
observed_outcome, model_version e contribution_audit. Chaves de tenant e timestamps de disponibilidade
são obrigatórios. Não armazenar segredos em logs.
Operação
Workers de ingestão e otimização assíncrona, filas com idempotência, orçamento por job, observabilidade
de latência e custo, alarmes de falha, fallback e replay. O dashboard expõe custo previsto, incerteza,
restrições e justificativa derivada dos coeficientes; não depende de explicações textuais geradas pelo Jev.


## Página 19


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
19
Q-FLOW / 16 / VIABILIDADE ECONÔMICA
Modelo de negócio e unit economics
Começar com receita SaaS B2B e comprovar economia incremental antes de escalar
aquisição.
A Q-Flow vende decisões e integração, não tempo de QPU. Priorizar um piloto remunerado ou com escopo
claro, implantação de dados e contrato por frota ou volume de otimizações. Data Partnership oferece
créditos por contribuição de qualidade, com teto e prazo. A concorrência exige demonstrar benefício frente
ao roteirizador atual [8].
Hipótese ilustrativa
Valor
Interpretação
Frota
100 veículos
Cliente hipotético
Combustível por veículo/mês
R$ 12.000
Gasto mensal total R$ 1,2 milhão
Redução de gasto: 1% / 3% / 5%
R$ 12 / 36 / 60 mil
Economia bruta mensal hipotética
Assinatura + implantação
R$ 10 mil/mês + R$ 20 mil
Preço-teste, sem validação de
mercado
Desconto Partner
50% implantação + 25%
mensal
R$ 10 mil + R$ 7,5 mil/mês
Economia do cliente no primeiro ano
A 3% de redução hipotética de combustível, a economia bruta anual seria R$ 432 mil. O plano padrão
custaria R$ 140 mil no primeiro ano, resultando em R$ 292 mil antes de outros custos de adoção; o Partner
custaria R$ 100 mil, deixando R$ 332 mil. São cenários aritméticos, não projeções de receita ou eficácia.
Custo da Q-Flow por decisão
CM = Cinferência + Csolvers + Cdados + Cinfra + Cvalidação + Camortização
O custo do Jev depende de volume, preço contratado, tamanho de entrada e reprocessamento. A QPU
pode impor filas, custo variável e limites de orçamento. A métrica decisiva é custo total por decisão viável,
incluindo treinamento, ingestão e validação. O desconto só deve ser concedido se o valor esperado da
contribuição superar custo de limpeza e margem sacrificada. Validar disposição de pagar em entrevistas e
propostas reais.
Mercado endereçável
Não estimamos TAM/SAM/SOM sem pesquisa de segmentação verificável. O primeiro objetivo é
encontrar clientes com telemetria de qualidade, problema recorrente e benefício mensurável.


## Página 20


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
20
Q-FLOW / 17 / EXPERIMENTOS
Metodologia de validação
Separar o valor da informação, da otimização, da memória e do processamento quântico.
Experimento
Configuração
Hipótese testada
A
Roteirizador por distância
Referência simples
B
Clássico multivariável, mesmo domínio
Valor da modelagem
C
B + Jev calibrado/ML
Valor incremental contextual
D
QAOA no mesmo QUBO de B
Qualidade e custo quânticos
E
QAOA no mesmo QUBO de C
Interação IA + Qiskit
F
E ou C + cache/warm-start
Eficiência computacional e qualidade
Usar as mesmas instâncias, restrições, escalas, versões e sementes entre solucionadores. Para instâncias
pequenas, enumerar o ótimo; para maiores, registrar limites/solução clássica e orçamento de tempo.
Avaliar simulador ideal e hardware separadamente, registrando queue time, transpile, shots, profundidade,
portas de dois qubits, energia e taxa de soluções válidas. Não usar custo de uma simulação clássica como
prova de vantagem quântica.
Métricas de decisão
gap = (Fsolução − Fótimo) / |Fótimo| (quando Fótimo ≠ 0)
Métricas: custo esperado e realizado, combustível, pontualidade, viabilidade, gap/regret, latência p50/p95,
chamadas Jev, tempo QPU, taxa de reutilização válida e custo total por decisão. Avaliar intervalos de
confiança, variabilidade por seed e subgrupo. Para ótimos desconhecidos, comparar com limites ou melhor
solução de referência, sem rotular o gap como exato.
Avaliação de dados históricos
Comparar modelo sem histórico, modelo privado, modelo global e global especializado. Separar
treino/teste temporalmente e por cliente. Iniciar shadow mode sem alterar decisões reais; medir previsão e
viabilidade. Em piloto controlado, alternar políticas apenas em cenários seguros e comparáveis; medir
economia real e efeitos sobre SLA.


## Página 21


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
21
Q-FLOW / 18 / MVP
Um caminho incremental de execução
Para o Challenge, o objetivo é demonstrar a ideia; para a startup, obter evidência
reproduzível.
Etapa
Entregável técnico
Critério de avanço
1. Formulação
Dois veículos / duas rotas; QUBO e Ising.
Enumeração exata e testes de
equivalência.
2. Dados
Dataset sintético com contexto, candidatos e
resultados.
Reprodução por seed, sem dados
pessoais.
3. Clássico
Gerar e validar planos com custos multivariáveis.
100% de planos publicados respeitam
regras testadas.
4. Quântico
QAOA em simulador; QPU se houver acesso.
Log de gap, viabilidade, shots e custo.
5. Jev/ML
Adapter real ou mock explícito; calibração.
Holdout temporal e baseline sem Jev.
6. Memória
Cache, similaridade e warm-start.
Redução de reprocessamento sem
perda acima de tolerância.
7. Piloto
Importação de parceiro, shadow mode e teste
controlado.
Economia real, SLA e viabilidade
comercial.
Caso demonstrativo
Três veículos, dois ou três planos por veículo, cargas diferentes, topografia de região montanhosa, horários
e capacidade de doca. Dados geográficos podem ser reais quando licenciados; custos de frota e telemetria
simulados devem ser rotulados. Com três veículos e duas escolhas, o exemplo direto tem três bits; ao
aumentar candidatos, um modelo one-hot cresce com número de planos e interações.
Escalabilidade
Uma formulação ingênua de conexões dirigidas para n entregas e um depósito tem n(n+1) variáveis antes
de restrições e veículos: 30 para cinco entregas, 110 para dez, 420 para vinte. Em vez de mapear todo o
VRP, a Q-Flow gera candidatos classicamente, decompõe por região/turno e aplica QAOA a conflitos
pequenos. Conectividade, profundidade, ruído, orçamento e filas limitam escala; medir essas limitações.
Critério do Challenge
O regulamento não exige programação [1]. Não apresentar mock, simulação ou plano de trabalho como
implantação real.


## Página 22


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
22
Q-FLOW / 19 / RISCOS
Riscos, mitigação e decisões abertas
A tese deve permanecer útil mesmo quando uma hipótese técnica não for confirmada.
Risco
Consequência
Mitigação
QAOA sem ganho
Sem vantagem prática sobre
clássico
Fallback e estudo de subproblemas; critério de
desligamento.
Jev mal calibrado
Custos enviesados ou falsas
probabilidades
Holdout, calibração, abstention e baseline sem
Jev.
Histórico enviesado
Reprodução da política anterior
Diversidade, avaliação por grupos, piloto
controlado.
Cache obsoleto
Decisão inválida após mudança
Hash/versionamento, TTL, invalidação e
validação.
Integração de dados cara
Margem negativa no onboarding
Auditoria amostral, conectores e escopo de
implantação.
Dados pessoais/segredos
Exposição, risco legal e comercial
Segregação, minimização e revisão jurídica.
Dependência de fornecedor
Preços, disponibilidade ou API
mudam
Interfaces substituíveis, orçamento e fallback.
Complexidade prematura
MVP demora ou não valida
hipótese
Entrega incremental e medir cada contribuição.
Decisões assumidas nesta versão
Q-Flow é nome provisório; a arquitetura CDC/ALE/HIE/ASR é uma proposta de design. Escolhemos foco
rodoviário B2B, geração clássica de candidatos, QAOA experimental, ML supervisionado, integração por
API e Data Partnership voluntário. Nenhum preço foi validado com clientes; não há dados reais de
telemetria disponíveis, nem confirmação de acesso à API Jev ou QPU. A composição da equipe e campos
finais do formulário permanecem pendentes.
Conclusão
O potencial da Q-Flow é construir um sistema de decisões interdependentes com custos calibrados,
reaproveitamento computacional e aprendizado de operações. A logística é o primeiro domínio, e o
compilador pode futuramente ser estudado em energia, indústria e alocação de recursos. A tese de valor
comercial é independente de uma promessa de superioridade quântica; o estudo com Qiskit é uma
investigação específica e mensurável.


## Página 23


Q-FLOW  •  WHITE PAPER 2.0  /  QUANTUM PITCH 2026
23
Q-FLOW / REFERÊNCIAS
Fontes e declaração de IA
Referências técnicas consultadas e transparência do processo de elaboração.
[1] Organização Qiskit Fall Fest 2026. Abertura - Qiskit Fall Fest 2026 (slides de 24/11/2026); regras e entrega. Acessar fonte.
[2] Computers & Operations Research (2024). The pollution-routing problem with speed optimization and uneven topography.
Acessar fonte.
[3] IBM Quantum Documentation. Quantum approximate optimization algorithm. Acessar fonte.
[4] Qiskit Optimization. Vehicle Routing. Acessar fonte.
[5] Egger, Mareček e Woerner (2021). Warm-starting quantum optimization. Quantum 5, 479. Acessar fonte.
[6] IJCAI (2021). Contrastive Losses and Solution Caching for Predict-and-Optimize. Acessar fonte.
[7] Jev / TypeSafe AI. Documentação de decisões tipadas (README do SDK). Acessar fonte.
[8] PTV Logistics. Routing API: custos, restrições de veículos, trânsito e emissões. Acessar fonte.
[9] scikit-learn. Probability calibration. Acessar fonte.
[10] IBM Quantum Documentation. Warm-start QAOA with the Optimization Mapper Qiskit addon. Acessar fonte.
[11] Copernicus Data Space Ecosystem. Digital Elevation Model (GLO-30 / GLO-90). Acessar fonte.
[12] ANP. Série histórica de preços de combustíveis (dados abertos). Acessar fonte.
[13] Su et al. (2020). Doubly robust off-policy evaluation with shrinkage. ICML. Acessar fonte.
[14] Brasil. Lei nº 13.709/2018 (LGPD), texto compilado. Acessar fonte.
Declaração de utilização de inteligência artificial
O ChatGPT foi utilizado como apoio na pesquisa de referências, organização do estudo, formulação
matemática didática, desenho de arquitetura, elaboração de diagramas, redação e revisão dos materiais. As
decisões de produto foram construídas a partir das propostas do participante. A equipe deve revisar,
conferir e assumir responsabilidade pelo material submetido. Jev e Qiskit são tecnologias propostas para a
solução; não houve validação de integração em produção ou execução quântica real neste estudo.
Links consultados ou referenciados para desenvolvimento em 25/11/2026. O estudo não representa aprovação institucional da
IBM ou FIAP.
