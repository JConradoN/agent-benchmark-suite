# Agent Benchmark Suite — Resultados v0.1

**Data:** 2026-05-18  
**Modelos testados:** `gemma4:e4b-it-q4_K_M` (9.7B MoE) vs `gemma4:26b-a4b-it-q4_K_M` (26B MoE 4B ativos)  
**Infraestrutura:** fox-server — Xeon E5-2696 v3, 2× RTX 3060 12GB, 128GB RAM  
**Provider:** Ollama direto (`http://localhost:11434`), 3 runs por cenário  

---

## O que foi testado

O ABS v0.1 testa **modelos diretamente via Ollama API**, simulando o contexto de ferramenta de cada agente. O runner injeta as definições de tools do perfil correspondente (AURELIA_TOOLS ou HERMES_TOOLS), mas **não invoca os binários reais** da Aurelia (Go) nem do Hermes (Python).

O que o M-series compara hoje é o comportamento do **mesmo modelo** com dois conjuntos diferentes de tools — não a performance dos frameworks em si. Isso será corrigido na v0.2 com providers dedicados para cada framework (ver seção Roadmap).

---

## Dimensões de pontuação

| Dimensão | Escala | Critério |
|----------|--------|----------|
| QUAL | 0–4 | Correspondência de keywords ou validação JSON/schema |
| TOOL | 0–4 | Tool call correta com parâmetros esperados |
| LAT  | 0–4 | <3s=4, <8s=3, <20s=2, <60s=1, >60s=0 |

---

## Resultados completos — última rodada (pós-correção de cenários)

### T-series — Tool Selection

| Cenário | Descrição | e4b TOOL | e4b LAT | e4b ms | 26b TOOL | 26b LAT | 26b ms |
|---------|-----------|----------|---------|--------|----------|---------|--------|
| T1 | Escolha de tool por semântica (health_check) | 4 | 4 | 2.907 | 4 | 2 | 9.023 |
| T2 | Escolha de tool por semântica (shell_exec) | 4 | 4 | 2.187 | 4 | 4 | 3.399 |
| T3 | Parâmetros corretos (analyze_url) | 4 | 4 | 2.839 | 4 | 4 | 3.678 |
| T4 | Tool call com parâmetros complexos (cron_create) | 4 | 3 | 6.770 | 4 | 2 | 13.604 |
| T5 | Escolha entre tools similares (file_read vs shell_exec) | 4 | 4 | 2.348 | 4 | 4 | 2.988 |
| T6 | Recusa de tool irrelevante (sem tool = correto) | 4 | 4 | 2.146 | 4 | 4 | 2.822 |

**Achado:** Seleção de tool perfeita para ambos os modelos. A e4b é consistentemente mais rápida — T1 é o caso mais extremo: 2.9s vs 9.0s. A latência extra da 26b não traduz em melhor qualidade de seleção.

---

### C-series — Chain (tool use sequencial)

| Cenário | Descrição | e4b QUAL | e4b LAT | e4b ms | 26b QUAL | 26b LAT | 26b ms |
|---------|-----------|----------|---------|--------|----------|---------|--------|
| C1 | URL analysis → resumo | 4 | 2 | 11.838 | 4 | 2 | 13.235 |
| C2 | health_check → diagnóstico → recomendação | 4 | 2 | 11.641 | 3 | 2 | 9.940 |
| C3 | 2 analyze_url sequenciais (mocks rotativos) | 4 | 3 | 8.535 | 4 | 1 | 20.206 |
| C4 | shell_exec → conta containers (9) | 2 | 4 | 2.512 | 3 | 4 | 2.615 |
| C5 | Loop detection — deve parar após 1 tool call | 4 | 4 | 2.350 | 4 | 4 | 2.377 |

**Notas:**

- **C2:** antes da correção de prompt, e4b respondia sem chamar a tool (QUAL=1). Após tornar explícito "Use as ferramentas disponíveis", e4b chegou a 4/4. A 26b foi menos sensível à ambiguidade (3/4 mesmo antes).
- **C3:** 26b demorou 20s porque tentou raciocinar mais antes de chamar as tools. e4b foi direto. LAT=1 para 26b (>20s).
- **C4:** ambos mencionaram "9 containers" corretamente, mas nenhum usou a palavra "nove" em português — keyword ausente derrubou o score para 2–3. Indica limitação do scoring por keywords, não do modelo.
- **C5:** ambos pararam corretamente após 1 tool call. Sem loops.

---

### L-series — Long Context

| Cenário | Descrição | e4b QUAL | e4b LAT | e4b ms | 26b QUAL | 26b LAT | 26b ms |
|---------|-----------|----------|---------|--------|----------|---------|--------|
| L1 | Retenção turn 1 → turn 5 (128GB RAM) | 4 | 4 | 728 | 4 | 4 | 817 |
| L2 | Consistência aritmética 8 turns (€270 restante) | 4 | 3 | 3.210 | 4 | 4 | 2.069 |
| L3 | Qualidade técnica após 10 turns (modelo para RTX 3060) | 3 | 2 | 9.166 | 1 | 2 | 13.421 |

**Notas:**

- **L1 e L2:** ambos perfeitos em retenção factual e aritmética simples.
- **L3:** diferença significativa. e4b manteve coerência técnica ao longo de 10 turns (QUAL=3), mencionando modelos eficientes, MoE e Q4. A 26b degradou notavelmente (QUAL=1) — respondeu a pergunta final com menos precisão técnica, sugerindo maior sensibilidade ao contexto acumulado.

---

### M-series — Multi-agent (comparação de perfis de tools)

| Cenário | Descrição | e4b QUAL | e4b LAT | e4b ms | 26b QUAL | 26b LAT | 26b ms |
|---------|-----------|----------|---------|--------|----------|---------|--------|
| M1-A | URL analysis — perfil Aurelia | 3 | 3 | 4.493 | 3 | 3 | 5.771 |
| M1-H | URL analysis — perfil Hermes | 3 | 3 | 4.649 | 3 | 3 | 5.581 |
| M2-A | Diagnóstico de sistema — perfil Aurelia | 3 | 2 | 11.697 | 4 | 2 | 12.631 |
| M2-H | Diagnóstico de sistema — perfil Hermes | 4 | 2 | 16.140 | 4 | 2 | 14.003 |

**Notas:**

- **M1-A vs M1-H:** comportamento idêntico nos dois perfis — o modelo não diferencia o conjunto de tools disponível quando a tarefa é a mesma. Ambos ficaram em 3/4 porque os bullets gerados nem sempre usaram os keywords exatos.
- **M2-A:** 26b foi mais proativa no uso da tool com prompt implícito. e4b precisou do prompt mais explícito (mesma correção do C2).
- **M2-H:** e4b ficou mais lento por gerar resposta mais extensa após o shell_exec. Ambos chegaram a 4/4.
- **Limitação atual:** M-series compara o **mesmo modelo com perfis de tool diferentes**, não Aurelia vs Hermes como frameworks. A comparação real de framework está planejada para v0.2.

---

### Q-series — Quality (sem tools)

| Cenário | Descrição | e4b QUAL | e4b LAT | e4b ms | 26b QUAL | 26b LAT | 26b ms |
|---------|-----------|----------|---------|--------|----------|---------|--------|
| Q1 | Trade-offs RTX 3060 vs RTX 4090 para 7B-9B | 3 | 1 | 20.172 | 2 | 2 | 11.894 |
| Q2 | Conformidade JSON (gemma4:e4b) | 4 | 4 | 1.192 | 4 | 4 | 1.145 |
| Q3 | Retenção de contexto técnico 4 turns | 4 | 3 | 5.446 | 3 | 2 | 12.232 |
| Q4 | Diagnóstico de log (CUDA OOM) | 3 | 2 | 10.933 | 3 | 2 | 12.939 |

**Notas:**

- **Q1 — caso especial:** a 26b deu a resposta semanticamente **correta** ("RTX 4090 é desnecessário para 7B-9B") enquanto a e4b recomendou comprar a 4090. Apesar disso, a e4b pontuou mais (3 vs 2) por acertar mais keywords. Isso expõe uma limitação do método keyword\_match para raciocínio de trade-off: o scoring não captura a direção do argumento. Candidato a um cenário com `llm_judge` na v0.2.
- **Q2:** ambos perfeitos em conformidade de formato JSON.
- **Q3:** e4b melhor em retenção multi-turn (4 vs 3) e significativamente mais rápido (5.4s vs 12.2s).

---

## Resumo comparativo

### Por série (média de QUAL ou TOOL, última rodada)

| Série | e4b avg | 26b avg | Vencedor |
|-------|---------|---------|----------|
| T (tool selection) | 4.0 / 4 | 4.0 / 4 | Empate |
| C (chain) | 3.6 / 4 | 3.6 / 4 | Empate |
| L (long context) | 3.7 / 4 | 3.0 / 4 | **e4b** |
| M (multi-agent profile) | 3.5 / 4 | 3.75 / 4 | 26b leve |
| Q (quality) | 3.5 / 4 | 3.0 / 4 | **e4b** |

### Latência média por série

| Série | e4b avg ms | 26b avg ms | Speedup e4b |
|-------|-----------|-----------|-------------|
| T | 3.210 | 5.952 | **1.85×** |
| C | 6.983 | 9.595 | **1.37×** |
| L | 4.368 | 5.436 | **1.24×** |
| M | 9.245 | 9.497 | **1.03×** |
| Q | 9.686 | 9.315 | 0.96× |

### Throughput (tok/s)

Ambos os modelos operam entre 67–71 tok/s — confirmando que o gargalo é o hardware (GPU), não o tamanho do modelo. A diferença de latência vem do **número de tokens gerados**, não da velocidade de geração.

---

## Achados principais

1. **Tool selection é igual:** ambos os modelos selecionam tools corretamente em 100% dos cenários T-series. Não há vantagem da 26b em "entender" as tools.

2. **e4b é mais rápido e gera menos tokens:** 1.2–1.9× mais rápido nos cenários com tool use. Isso é relevante em agentes onde múltiplas chamadas encadeadas somam latência.

3. **e4b superior em contexto longo:** L3 (QUAL 3 vs 1) mostra que a e4b degrada menos ao longo de 10 turns de conversa técnica.

4. **26b mais proativa com prompts implícitos:** M2-A e C2 (antes das correções) mostraram que a 26b é menos dependente de instruções explícitas para usar tools. Isso pode ser comportamento de treinamento, não diferença de capacidade — e é corrigível com engenharia de prompt.

5. **Keyword scoring tem limites:** Q1 pontuou e4b mais alto mesmo com resposta semanticamente errada. Cenários de raciocínio com direção de argumento precisam de `llm_judge`.

6. **C4 revela comportamento linguístico:** ambos os modelos responderam "9 containers" em inglês/numerais mas não em português ("nove"). O cenário C4 será refinado para aceitar ambas as formas na v0.2.

---

## O que NÃO foi testado (v0.1)

| Dimensão ausente | Impacto |
|-----------------|---------|
| Aurelia (binário Go real) | Overhead de sessão, memória 3 camadas, MCP latency |
| Hermes (daemon Python real) | System prompt próprio, history management, skill loading |
| Comparação modelo × framework | Não sabemos se e4b dentro do Hermes se comporta diferente de e4b direto |
| Multi-model (e4b + 26b em paralelo) | Dual GPU serving não testado |
| Consistência entre runs | Variância não analisada — 3 runs por cenário, sem análise estatística |

---

## Roadmap v0.2

### Priority 1 — Providers reais de framework

**Hermes Provider** (mais simples):
- Chamar `hermes chat` via subprocess ou endpoint HTTP do daemon
- Enviar turns do cenário sequencialmente
- Capturar resposta final e tool calls registradas pelo framework

**Aurelia Provider** (requer interface de teste):
- Aurelia é um bot Telegram — precisamos de uma rota de chat HTTP sem Telegram
- Opção A: endpoint `/api/chat` adicionado ao binário Go para testes
- Opção B: usar a Telegram Bot API com conta de teste dedicada

Isso vai habilitar a matriz completa:

```
                    gemma4:e4b   gemma4:26b
Ollama direto           ✓           ✓        ← v0.1
Aurelia framework       ?           ?        ← v0.2
Hermes framework        ?           ?        ← v0.2
```

### Priority 2 — Melhorias de scoring

- `llm_judge` para cenários de raciocínio (Q1, Q4) usando e4b como juiz
- Keyword normalization: aceitar "9" ou "nove", "containers" ou "contêineres"
- Score de variância: desvio padrão entre os 3 runs por cenário

### Priority 3 — Novos cenários

- **T-series T7–T8:** tool com parâmetros opcionais; recusa por tool indisponível
- **C-series C6:** chain de 3 tools sequenciais com resultado dependente
- **M-series M3:** mesmo task, modelo diferente, framework diferente (após providers v0.2)
- **Q-series Q5:** geração de código com verificação de sintaxe

---

## Referências

- Código fonte: https://github.com/JConradoN/agent-benchmark-suite
- Escala QUAL/TOOL/LAT 0–4: consistente com llms-on-prem S1–S4
- Hermes: https://hermes-agent.org/
- Aurelia: repositório interno fox-server (`~/.aurelia/`)
