# Q-Flow | Roteiro final de vídeo v2.1

**Quantum Pitch 2026 — IBM + FIAP — 25/11/2026**

**Duração máxima: 3 minutos.** Ensaiar com cronômetro, ajustar pausas e cortar se necessário. Objetivo: finalizar a locução até 02:55 e reservar 5 s à cartela. Os tempos por cena são guias de edição, não duração medida.

## 00:00–00:24 | O problema

**Visual:** Slides 1–2; caminhão na serra, sobreposição de carga, inclinação e diesel.

**Locução:** A rota mais curta nem sempre é a mais barata. Na logística, peso, topografia, preço do combustível, clima e prazo de entrega influenciam uns aos outros. Uma decisão que parece eficiente para um caminhão pode aumentar o custo de toda a frota. É esse problema que queremos resolver.

## 00:24–00:51 | A proposta

**Visual:** Slides 3–5; mostrar fluxo de dados → Jev → ML → CDC.

**Locução:** A Q-Flow é uma plataforma de inteligência logística adaptativa, integrada aos sistemas de transporte existentes. Nossa proposta combina dados históricos e telemetria com o Jev, uma inteligência artificial de decisões estruturadas. Modelos de machine learning calibram essas avaliações, e nosso compilador transforma custos e interações em uma função matemática de otimização.

## 00:51–01:17 | A formulação

**Visual:** Slides 6–8; exibir QUBO e quatro estados; destacar 01 e 10.

**Locução:** Representamos as escolhas por variáveis binárias e suas dependências por termos quadráticos, em uma formulação QUBO. Usamos o Qiskit da IBM para convertê-la em um Hamiltoniano de Ising e executar o algoritmo QAOA. Em um cenário ilustrativo de dois caminhões, coordenar as rotas reduz o custo modelado de seiscentos e sessenta para seiscentos e dez reais.

## 01:17–01:49 | O resultado experimental

**Visual:** Slides 9–10; mostrar 4.096 shots, gráfico e backend; não mostrar credenciais.

**Locução:** E não ficamos apenas na teoria. Implementamos a prova de conceito e executamos o mesmo circuito em simulador ideal, simulador com ruído e no computador quântico IBM Kingston. Em quatro mil e noventa e seis medições físicas, obtivemos soluções globalmente ótimas em noventa e seis vírgula quarenta e seis por cento dos resultados. Isso demonstra a execução da nossa modelagem em hardware real, sem afirmar vantagem quântica.

## 01:49–02:15 | Aprendizado e eficiência

**Visual:** Slides 12–14; animar feedback, cache, similaridade e seleção de solver.

**Locução:** A arquitetura foi projetada para aprender com os resultados reais. A telemetria alimenta os modelos, permitindo calibrar previsões e recuperar soluções anteriores. Quando o contexto muda, queremos reprocessar apenas o necessário. O sistema seleciona entre memória, processamento clássico e quântico, conforme a qualidade esperada e o custo computacional.

## 02:15–02:43 | Mercado e dados

**Visual:** Slides 15–16; animação de parceria, modelo global e privado.

**Locução:** Nosso mercado inicial são transportadoras com operações recorrentes. O modelo comercial é uma assinatura B2B integrada ao TMS. Com o Data Partnership, propomos descontos em troca de acesso autorizado a históricos relevantes, permitindo pré-treinar modelos antes da implantação. Cada parceria pode ampliar o conhecimento da plataforma, respeitando a privacidade e a confidencialidade comercial.

## 02:43–02:55 | Fechamento

**Visual:** Slides 17–18; logo, mensagem final e referências.

**Locução:** O próximo passo é validar a economia em pilotos reais. Q-Flow: uma infraestrutura de decisões interdependentes que aprende com o mundo real e evolui com a computação quântica.

## 02:55–03:00 | Cartela final

**Visual:** Logo + nomes dos três integrantes + referência à PoC. Sem locução.

## Orientações de edição

- Priorize os slides 2, 4, 7, 9 e 15; não tente narrar os 18 slides.
- Identifique dois qubits, 4.096 shots e IBM Kingston; distinguir frequência amostral de probabilidade verdadeira.
- O ganho de R$ 50 (7,58%) decorre da coordenação no modelo ilustrativo, não da QPU.
- Não afirmar integração Jev/ML concluída, vantagem quântica, aprovação da IBM ou economia comercial.
- Declaração de IA: ChatGPT apoiou pesquisa/documentação; Cursor apoiou código/execução sob supervisão humana.
- Equipe de três integrantes confirmada; preencher nomes na cartela e formulário. Conferir a visibilidade do repositório antes de compartilhar.

**Fonte experimental:** [resultado QPU](../../results/quantum_poc_v0.1/ibm_quantum_results.json) e White Paper v2.1, pp. 24–26.
