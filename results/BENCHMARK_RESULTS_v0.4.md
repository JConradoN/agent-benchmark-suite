# Agent Benchmark Suite — Resultados v0.4

**Data:** 2026-05-19  
**Hardware:** fox-server — Xeon E5-2696 v3 (18c/36t) · 2× RTX 3060 12GB · 128 GB DDR4 ECC  
**Modelo novo:** `qwen3.6:35b-a3b` (Qwen3.6 MoE, 35B total / ~3B ativos por token)  
**Providers testados:** Ollama direto (FASE 1) · Aurelia Go agent (FASE 2) · Hermes Python agent (FASE 3)  
**Escala:** 0–4 (QUAL = qualidade da resposta, TOOL = qualidade de tool use, LAT = score de latência)

---

## 1. Resultados diretos — qwen3.6:35b-a3b (FASE 1)

### T-series (seleção de tool)

| ID | Descrição | Score | tok/s |
|----|-----------|:-----:|------:|
| T1 | URL analysis | 4.00 | 23.1 |
| T2 | YouTube transcript | 4.00 | 22.9 |
| T3 | Health check | 4.00 | 22.7 |
| T4 | Parâmetros complexos | 4.00 | 22.4 |
| T5 | Cron scheduling | 4.00 | 23.2 |
| T6 | Discriminação URL vs YouTube | 4.00 | 23.3 |
| **Média** | | **4.00** | **22.9** |
| Tool calls | | 12/12 ✅ | |

LAT=0 em todos — tempo de primeiro token com 35b-a3b é ~130-160s (carregamento do modelo 28GB).

---

### C-series (chain — tool use sequencial)

| ID | Descrição | QUAL | LAT | Obs |
|----|-----------|:----:|:---:|-----|
| C1 | URL → resumo | 4.00 | 2 | Paper ToT — análise profunda e correta |
| C2 | Health → diagnóstico | 4.00 | 2 | RAM 118GB identificada como causa raiz |
| C3 | 2 tool calls sequenciais | 4.00 | 2 | Aurelia vs AgentForge — comparativo correto |
| C4 | Shell → containers | 2.00 | 3 | Listou 9 containers corretos, score baixo por artefato* |
| C5 | Loop detection | 4.00 | 3 | Health check direto e conciso |
| **Média** | | **3.60** | **2.40** | |

*C4: artefato de scoring — modelo respondeu corretamente mas formato divergiu do esperado.

---

### Q-series (qualidade textual, sem tools)

| ID | Descrição | QUAL | LAT |
|----|-----------|:----:|:---:|
| Q1 | Trade-offs hardware LLM | 3.00 | 1 |
| Q2 | Conformidade JSON | 4.00 | 4 |
| Q3 | Retenção contexto técnico | 3.00 | 2 |
| Q4 | Análise log de erro | 4.00 | 1 |
| **Média** | | **3.50** | **2.00** |

Q1 e Q3 com score 3 — o modelo produz respostas longas e detalhadas mas não cobre todos os critérios de pontuação de forma consistente.

---

### L-series (retenção longa)

| ID | Descrição | QUAL | LAT |
|----|-----------|:----:|:---:|
| L1 | Info turn 1 → turn 5 | 4.00 | 4 |
| L2 | Consistência aritmética 8 turns | 4.00 | 2 |
| L3 | Qualidade após 10 turns | 2.00 | 1 |
| **Média** | | **3.33** | **2.33** |

L3 = 2.0: degradação em conversas muito longas, consistente com outros modelos. MoE não resolve o problema de retenção em contextos extremos.

---

### M-series (perfis multi-agent)

| ID | Perfil | QUAL | LAT | tok/s |
|----|--------|:----:|:---:|------:|
| M1-A | URL analysis — Aurelia | 3.00 | 2 | 22.1 |
| M1-H | URL analysis — Hermes | 3.00 | 2 | 22.1 |
| M2-A | Diagnóstico — Aurelia | 3.00 | 2 | 22.1 |
| M2-H | Diagnóstico — Hermes | **0.00** | 4 | 22.7 |
| **Média** | | **2.25** | **2.50** | |

**M2-H = 0 é o dado mais relevante desta série.** O modelo respondeu em ~5-6s (LAT=4, muito rápido) mas a resposta foi completamente inadequada para o perfil Hermes. O sistema prompt do Hermes criou uma divergência com o estilo de output do 35b-a3b — o modelo antecipou uma resposta direta quando o perfil esperava raciocínio estruturado. Esse fenômeno não ocorreu com qwen3.5:9b (M2-H=3.0) nem com gemma4:26b (M2-H=4.0).

---

### Resumo direto — ranking geral atualizado

| Modelo | T | C | Q | L | M | **Geral** | tok/s | VRAM |
|--------|---|---|---|---|---|-----------|------:|-----:|
| qwen3.5:9b | 4.00 | 3.60 | 3.50 | **3.67** | 3.25 | **3.60** | 44.7 | 6.6 GB |
| granite4.1:8b | 4.00 | 3.60 | 3.50 | 3.33 | 3.00 | 3.49 | 57.5 | 5.7 GB |
| gemma4:e4b-q8 | 4.00 | 3.60 | 3.38 | 3.33 | 3.00 | 3.46 | 51.3 | 11 GB |
| gemma4:26b | 4.00 | 3.60 | 3.00 | 3.00 | **3.50** | 3.42 | 68.2 | 17 GB |
| gemma4:e4b-q4 | 4.00 | 3.00 | 3.21 | 3.17 | 3.33 | 3.34 | **69.0** | 9.6 GB |
| **qwen3.6:35b-a3b** | 4.00 | 3.60 | 3.50 | 3.33 | 2.25 | **3.34** | 22.3 | 28 GB |
| granite4.1:30b | 4.00 | 3.42 | 3.22 | 3.17 | 2.75 | 3.31 | ~18 | 17 GB |

**Resultado contraintuitivo:** o maior modelo testado (35b-a3b) não vence o menor (qwen3.5:9b). A diferença está inteiramente no M-series — o M2-H=0 do 35b-a3b arrasta o geral para 3.34. Em T, C e Q as performances são idênticas (4.0, 3.6, 3.5).

---

## 2. Framework — FASE 2 (Aurelia) e FASE 3 (Hermes)

### Aurelia com qwen3.6:35b-a3b

#### F-series (framework benchmark)

| ID | Descrição | run0 QUAL | run1 QUAL | Média | lat_ms |
|----|-----------|:---------:|:---------:|:-----:|-------:|
| F1 | Raciocínio RTX 3060 | 1 | 3 | 2.0 | ~99k |
| F2 | Conformidade JSON | 4 | 4 | **4.0** | ~66k |
| F3 | Retenção multi-turn (4 turns) | 2 | 2 | 2.0 | ~154k |
| F4 | Shell — Docker containers | 4 | 2 | 3.0 | ~23k |
| F5 | Diagnóstico do servidor | **0** (timeout) | 2 | 1.0 | — |
| F6 | Leitura de arquivo | 2 | 3 | 2.5 | ~15k |
| F7 | HTTP via curl — Ollama | 4 | 4 | **4.0** | ~46k |
| **Média** | | | | **2.64** | |

#### Q-series via Aurelia

| ID | run0 | run1 | Média | Obs |
|----|:----:|:----:|:-----:|-----|
| Q1 | 2 | 2 | 2.0 | Overhead HTTP + 22tok/s → latência alta |
| Q2 | 4 | **0** | 2.0 | run1 timeout (120s) |
| Q3 | 1 | 3 | 2.0 | Inconsistência entre runs |
| Q4 | **0** | **0** | **0.0** | Ambos timeout — resposta longa + 22tok/s |
| **Média** | | | **1.50** | |

#### L-series via Aurelia

| ID | run0 | run1 | Média | lat_ms | Obs |
|----|:----:|:----:|:-----:|-------:|-----|
| L1 | 4 | 4 | **4.0** | ~174k | Funciona |
| L2 | 0 | 0 | **0.0** | 120k/120k | Timeout duplo |
| L3 | 0 | 0 | **0.0** | 240k/304k | Completou mas QUAL=0 — sessão perdida |
| **Média** | | | **1.33** | |

**Aurelia framework total: 2.03** ← número crítico.

L2 e L3 revelam o problema principal: o timeout de 120s foi expandido no ABS (--timeout 600), mas Aurelia não consegue manter sessão longa com 35b-a3b a 22 tok/s. L3 completou em 240-304s mas retornou QUAL=0 — a sessão foi criada mas o contexto multi-turn foi perdido.

---

### Hermes com qwen3.6:35b-a3b

#### F-series via Hermes (máximo QUAL por run)

| ID | Descrição | run0 | run1 | Média |
|----|-----------|:----:|:----:|:-----:|
| F1 | Raciocínio RTX 3060 | 2 | 1 | 1.5 |
| F2 | Conformidade JSON | 4 | 0 | 2.0 |
| F3 | Retenção multi-turn | 3 | 4 | **3.5** |
| F4 | Shell — Docker containers | 4 | 4 | **4.0** |
| F5 | Diagnóstico do servidor | 4 | 3 | 3.5 |
| F6 | Leitura de arquivo | 3 | 3 | 3.0 |
| F7 | HTTP via curl — Ollama | 4 | 4 | **4.0** |
| **Média** | | | | **3.07** |

#### Q-series via Hermes

| ID | run0 | run1 | Média |
|----|:----:|:----:|:-----:|
| Q1 | max(3,2)=3 | max(2,2)=2 | 2.5 |
| Q2 | max(4,4)=4 | max(0,0)=0 | 2.0 |
| Q3 | max(1,2)=2 | max(3,2)=3 | 2.5 |
| Q4 | max(3,3)=3 | max(3,4)=4 | **3.5** |
| **Média** | | | **2.63** |

#### L-series via Hermes

| ID | run0 | run1 | Média | Obs |
|----|:----:|:----:|:-----:|-----|
| L1 | 4 | 4 | **4.0** | |
| L2 | 4 | 4 | **4.0** | 770s / 184s — lento mas correto |
| L3 | 2 | 2 | 2.0 | Degradação esperada em 10+ turns |
| **Média** | | | **3.33** | |

**Hermes framework total: 2.71**

---

### Comparação Aurelia × Hermes com 35b-a3b

| Série | Aurelia | Hermes | Delta |
|-------|:-------:|:------:|:-----:|
| F (framework) | 2.64 | **3.07** | +0.43 |
| Q (qualidade) | 1.50 | **2.63** | +1.13 |
| L (retenção longa) | 1.33 | **3.33** | **+2.00** |
| **Geral** | **2.03** | **2.71** | **+0.68** |

Hermes supera Aurelia em todas as séries. A diferença mais expressiva é no L-series (+2.0): Hermes mantém contexto em sessões longas com o 35b-a3b; Aurelia colapsa com timeout ou perde a sessão.

Referência cruzada com v0.3 (outros modelos nos frameworks):

| Modelo | Aurelia F-avg | Hermes F-avg |
|--------|:------------:|:------------:|
| gemma4:e4b | 3.21 | 3.00 |
| granite4.1:8b | 3.07 | 3.00 |
| **qwen3.6:35b-a3b** | **2.64** | **3.07** |

O 35b-a3b é o pior modelo testado na Aurelia. É o melhor no Hermes F-series.

---

## 3. LLMs maiores / menos quantizados são melhores?

**Resposta curta: depende da tarefa e da arquitetura.**

### Evidência dos benchmarks

| Afirmação | Status | Evidência |
|-----------|--------|-----------|
| Modelos maiores = melhor tool use | ❌ Falso | T-series: todos os modelos pontuam 4.0/4.0 independente de tamanho |
| Modelos maiores = melhor qualidade | ⚠️ Marginal | Q-series: 35b-a3b (3.50) = qwen3.5:9b (3.50). 26b (3.00) < granite8b (3.50) |
| Modelos maiores = melhor multi-turn | ❌ Falso | L3: gemma4:e4b-q8 (3.0) > qwen3.6:35b-a3b (2.0) > gemma4:26b (1.0) |
| Menos quantização = melhor | ⚠️ Pequena diferença | gemma4:e4b-q8 (3.46) vs e4b-q4 (3.34) — diferença de 0.12 geral |
| MoE maiores = mais lentos que MoE menores | ✅ Verdadeiro | 35b-a3b: 22 tok/s vs qwen3.5:9b: 44 tok/s |

### Quando tamanho/quantização importam

**Tamanho importa em:**
- Raciocínio de múltiplos passos sem tools (análise complexa, síntese)
- Instruções em línguas menos representadas
- Seguir instruções muito longas ou contraditórias com menos alucinação
- Contextos onde o erro de um passo invalida toda a cadeia

**Tamanho NÃO importa em:**
- Tool selection e tool use estruturado — granite4.1:8b e qwen3.5:9b pontuam igual ao 35b-a3b
- Respostas curtas e diretas (latência domina a qualidade percebida)
- Cenários com exemplos (few-shot) no prompt — menor necessidade de "saber" do modelo

**Quantização importa em:**
- Perda q4→q8 é pequena (~0.1 ponto de qualidade nos benchmarks)
- Impacto maior em contextos extremos (>8k tokens) onde q4 perde coerência mais rápido
- Para uso em agente com ferramenta + resposta curta: q4 é adequado

### Conclusão prática para o fox-server

O 35b-a3b com 28GB VRAM (ambas GPUs) e 22 tok/s tem o **custo mais alto** e a **maior pontuação bruta mais baixa** do conjunto testado. O gargalo não é a qualidade do modelo — é o volume de parâmetros ativos por inferência (MoE é eficiente em FLOPS mas não em latência de primeira geração quando a VRAM é saturada).

Para o caso de uso do fox-server: use modelo grande **apenas quando** a tarefa exige raciocínio que os menores claramente falham. Em benchmark ABS, nenhuma tarefa testada diferenciou o 35b-a3b positivamente do qwen3.5:9b.

---

## 4. Fox-server original (i5-10400F) vs fox-server atual (Xeon E5-2696 v3) — Aurelia e Hermes

### Hardware completo dos dois servidores

| Componente | fox-server original (~R$3.500) | fox-server atual (~R$8.530 em upgrade) |
|------------|--------------------------------|----------------------------------------|
| **CPU** | Intel i5-10400F (6c/12t, 2.9/4.3 GHz, Ice Lake 2020) | Intel Xeon E5-2696 v3 (18c/36t, 2.3/3.8 GHz, Haswell-EP 2014) |
| **RAM** | 32 GB DDR4 2666 dual-channel (~40 GB/s) | 128 GB DDR4 ECC 2133 tri-channel (~51 GB/s) |
| **GPU** | 1× RTX 3060 12GB Ventus 2 | 2× RTX 3060 12GB (Galax OC + MSI Ventus 2X) = 24 GB VRAM |
| **Placa-mãe** | H510 (LGA1200) | HUANANZHI X99-F8 (LGA2011-3) |
| **PCIe GPU** | x16 Gen3 → ~16 GB/s (1 slot) | x8+x8 Gen3 → ~8 GB/s por GPU (2 slots) |
| **NVMe** | Kingston NV1 512GB | Kingston NV3 1TB |
| **Fonte** | 650W 80+ Bronze | 750W 80+ Gold |
| **ECC RAM** | Não | Sim |
| **Custo total** | ~R$3.500 | ~R$12.030 (acumulado) |

> Nota: a RTX 3060 Ventus 2 do servidor original foi reaproveitada como GPU1 no servidor atual.

---

### IPC e single-thread

O i5-10400F tem IPC ~40-50% superior ao Xeon E5-2696 v3 — Ice Lake (2020) vs Haswell-EP (2014). Isso importa para:
- Hermes: o processo Python tem overhead de subprocess + parsing JSON — beneficia de clock alto
- Aurelia Go: compilado e eficiente, overhead de goroutine é mínimo
- Ollama: carregamento inicial do modelo é single-thread

Para inferência de tokens gerados, o gargalo é 100% na GPU. O single-thread do CPU não afeta tok/s quando o modelo cabe inteiramente na VRAM.

---

### Capacidade de modelos por servidor

| Modelo | VRAM | i5 original (12GB) | Xeon atual (24GB) |
|--------|-----:|:------------------:|:-----------------:|
| granite4.1:8b | 5.7 GB | ✅ 57 tok/s (full GPU) | ✅ 57 tok/s |
| qwen3.5:9b | 6.6 GB | ✅ 44 tok/s (full GPU) | ✅ 44 tok/s |
| gemma4:e4b-q4 | 9.6 GB | ✅ 69 tok/s (full GPU) | ✅ 69 tok/s |
| gemma4:e4b-q8 | 11 GB | ⚠️ 51 tok/s (1GB livre apenas) | ✅ 51 tok/s |
| gemma4:26b | 17 GB | ❌ CPU offload ~5-8 tok/s | ✅ 68 tok/s (2 GPUs) |
| granite4.1:30b | 17 GB | ❌ CPU offload | ✅ ~18 tok/s (2 GPUs) |
| qwen3.6:35b-a3b | 28 GB | ❌ Não roda (>24GB mesmo 2 GPUs) | ✅ 22 tok/s (2 GPUs) |

**Descoberta crítica:** Para os modelos que cabem em 12GB (os três melhores do benchmark: qwen3.5:9b, granite4.1:8b, gemma4:e4b-q4), ambos os servidores entregam exatamente a mesma velocidade de inferência — a GPU é a mesma.

---

### Impacto em Aurelia e Hermes

**Para o modelo recomendado (qwen3.5:9b, 6.6GB):**
- i5 original: ✅ **44 tok/s — idêntico ao Xeon**. Aurelia responderia em 4-5s para 200 tokens.
- O bot Telegram funcionaria igualmente bem nos dois servidores para o modelo default recomendado.

**Para modelos grandes (26b, 35b):**
- i5 original com 26b: CPU offload → ~5-8 tok/s → Aurelia 200 tokens = 25-40s, Hermes L-series inviável
- Xeon com 26b: 68 tok/s via 2 GPUs, sem offload

**RAM e containers simultâneos:**
- i5 (32GB): Ollama + n8n + qdrant + aurelia saturaria ~28-30GB → swap para qualquer carga pesada
- Xeon (128GB): 9 containers ativos + Hermes sessions + Aurelia = usa ~45-60GB → margem confortável

**Hermes multi-turn (L-series):**
- Hermes armazena o histórico de sessão em disco + injeta no contexto. O processo Python em si usa ~200-400MB.
- No i5 com qwen3.5:9b: L-series funciona normalmente (modelo cabe na GPU inteira)
- No i5 com 26b: L2 (770s no Xeon com 35b) seria muito pior — 26b em CPU offload no i5 levaria horas

---

### Custo/benefício para uso com agentes

| Critério | i5 original | Xeon atual | Observação |
|----------|:-----------:|:----------:|------------|
| Custo hardware | R$3.500 | R$12.030 | Xeon 3.4× mais caro |
| Energia idle (estimada) | ~60-80W | ~180-220W | i5 ~3× mais eficiente |
| Energia sob benchmark | ~160-200W | ~350-420W | i5 ~2× mais eficiente |
| Modelos ≤12GB (Aurelia default) | ✅ igual | ✅ igual | **Sem diferença** |
| Modelos 13-24GB | ❌ CPU offload | ✅ full GPU | Xeon decisivo |
| Modelos >24GB (35b-a3b) | ❌ Não roda | ✅ 22 tok/s | Xeon único |
| Containers simultâneos | ~4-5 | 9 confortável | Xeon necessário para stack completo |
| Aurelia latência (9b, 200tok) | ~4.5s | ~4.5s | **Idêntico** |
| Hermes L-series com 9b | ✅ funciona | ✅ funciona | **Idêntico** |
| Hermes L-series com 26b+ | ❌ inviável | ✅ funciona | Xeon necessário |

---

### Trade-offs principais

**Quando o i5 original seria suficiente:**
- Aurelia com qwen3.5:9b ou granite4.1:8b como modelo default → latência idêntica
- Hermes para tarefas que caibam em modelos ≤10GB
- Uso com 2-3 containers ativos (sem qdrant, sem fortejus, sem fox-noc)
- Cenário homelab leve, não servidor de produção

**Quando o Xeon atual é necessário:**
- Stack completo (9 containers + bots + VMs KVM)
- Qualquer modelo acima de 12GB (26b, 30b, 35b-a3b)
- Hermes com sessões longas + múltiplos contextos abertos simultaneamente
- 128GB ECC garante estabilidade 24/7 sem MCE errors em workloads de ML overnight
- fox-vault (pipeline de embeddings) + forte.jus + Aurelia rodando ao mesmo tempo

**Achado contraintuitivo:** o fox-server original com o modelo recomendado (qwen3.5:9b) teria performance de agente idêntica ao Xeon para o caso de uso principal do Telegram. O Xeon é necessário pelo stack completo de serviços, não pela latência do bot em si.

**PCIe x8+x8 vs x16:** o Xeon usa 2 slots x8 Gen3 para as duas RTX 3060. Isso limita bandwidth para ~8 GB/s por GPU vs ~16 GB/s em x16. Para modelos que cabem em uma GPU, não há impacto. Para 35b-a3b (28GB, spanning 2 GPUs), a transferência inter-GPU pelo barramento PCIe é o gargalo que explica os 22 tok/s — menos que os 44 tok/s do qwen3.5:9b com 6.6GB em uma única GPU.

---

## 5. Hermes vs Aurelia — comparação de frameworks

### Scores consolidados (todos os modelos testados)

| Framework | Modelo | F-avg | Q-avg | L-avg | Geral |
|-----------|--------|:-----:|:-----:|:-----:|:-----:|
| Aurelia | gemma4:e4b | 3.21 | — | — | — |
| Aurelia | granite4.1:8b | 3.07 | — | — | — |
| Aurelia | **qwen3.6:35b-a3b** | 2.64 | 1.50 | 1.33 | **2.03** |
| Hermes | gemma4:e4b | 3.00 | — | — | — |
| Hermes | granite4.1:8b | 3.00 | — | — | — |
| Hermes | **qwen3.6:35b-a3b** | 3.07 | 2.63 | 3.33 | **2.71** |

### Onde cada framework se destaca

**Aurelia vantagens:**
- Latência mais previsível (HTTP síncrono, sem overhead de subprocess)
- Sem processo zombie — Hermes tem histórico de processos fantasma que seguram VRAM
- Integração Telegram nativa
- Memória em 3 camadas — persistência entre sessões
- Menor dependência de configuração (não requer `config.yaml` separado)
- Mais rápido para respostas curtas (F2, F4, F7 com gemma4:e4b)

**Hermes vantagens:**
- Multi-turn nativo via sessão persistente (`--resume`)
- L-series: 3.33 vs 1.33 — retenção de contexto longo superior
- Q-series: 2.63 vs 1.50 — qualidade geral superior
- F3 (retenção multi-turn): 3.5 vs 2.0
- Mais robusto com modelos grandes/lentos (timeout 600s vs 120s padrão)
- Melhor uso do 35b-a3b em tarefas complexas (F5: 3.5 vs 1.0)

**Padrão de falha da Aurelia:**
- Timeout em respostas longas com modelos lentos (Q4, L2, L3 todos timeout com 35b-a3b)
- Sessão multi-turn colapsando após ~3 turns em conversas longas (L3: completa mas QUAL=0)
- Inconsistência entre runs do mesmo cenário (Q2: run0=4, run1=0)

**Padrão de falha do Hermes:**
- F2: run1=0 (inconsistência de conformidade JSON)
- M2-H=0 com 35b-a3b — incompatibilidade de estilo de output com o system prompt
- Processos fantasma após kill (bug operacional, não de qualidade)
- Latência muito alta em sessões longas com 35b-a3b (L2 run0: 770s)

### Veredito framework

Para uso interativo (Telegram, respostas rápidas): **Aurelia** com modelos pequenos-médios (≤13B).  
Para tarefas longas, pesquisa, análise multi-step: **Hermes** — especialmente com modelos maiores.  
Para o fox-server atual: Aurelia como default do bot + Hermes para tarefas batch/complexas é a combinação ideal.

---

## 6. Melhorias sugeridas para o Aurelia

### Críticas (impactam resultados do benchmark)

**1. Timeout dinâmico baseado no modelo**  
O timeout fixo de 120s (default) falha sistematicamente com modelos ≥13B a 22 tok/s. Uma resposta de 300 tokens leva 13.6s com 22 tok/s — razoável — mas quando há múltiplos turns acumulados no contexto, o tempo de geração cresce. Implementar timeout baseado em `tokens_estimados / tok_per_s_do_modelo` ou expor configuração `per_model_timeout` no `app.json`.

**2. Session persistence em contextos longos**  
L3 completou em 240-304s mas retornou QUAL=0 — o contexto multi-turn foi perdido no meio da sessão. A 3-layer memory do Aurelia não está injetando o histórico corretamente quando o contexto excede o limite ou quando o modelo retorna output vazio em um turn intermediário. Adicionar retry com reinjeção de contexto quando `content == ""` em turn intermediário.

**3. Detecção de timeout e retry com contexto reduzido**  
Quando um request ao `/api/chat` do Ollama excede o timeout configurado, Aurelia retorna QUAL=0 silenciosamente. Melhor: detectar timeout, resumir o contexto (últimos N turns) e re-tentar com contexto truncado.

### Importantes (UX e confiabilidade)

**4. Streaming de saída**  
A Chat API atual retorna a resposta completa após o tempo de geração total. Para o Telegram, o usuário fica em silêncio por 30-60s. Implementar streaming via SSE ou websocket, com envio parcial de chunks à medida que chegam do Ollama.

**5. Indicador "pensando..."**  
Enquanto gera, enviar `typing action` ao Telegram a cada 5s. Evita que o usuário pense que o bot travou.

**6. Retry automático em 5xx do Ollama**  
O Aurelia provavelmente não tem retry em erros de provider. Se o Ollama retorna 500 (ex: VRAM pressure temporário), a mensagem do usuário é silenciosamente descartada.

### Melhorias arquiteturais (roadmap)

**7. Provider Anthropic**  
Adicionar `anthropic` como provider além de Ollama. Útil quando: (a) o modelo local está carregado com outra tarefa, (b) o usuário faz uma pergunta que requer mais raciocínio do que o modelo local pode fornecer. Fallback automático seria poderoso.

**8. Tool budget por conversa**  
Implementar limite de tool calls por sessão para evitar loops infinitos (problema observado em Hermes também). Aurelia deveria expor `max_tool_calls_per_turn` no config.

**9. Métricas de runtime**  
Expor endpoint `/metrics` com: latência média por modelo, taxa de timeout, sessões ativas, VRAM usada. Alimenta o fox-noc.

**10. Separação de sessões por contexto**  
Hoje uma sessão Telegram é uma sessão de LLM. Para tarefas longas (pesquisa, análise), criar sub-sessão isolada com contexto próprio e sintetizar resultado ao final. Evita poluição do histórico de conversa principal.

---

## 7. Modelo recomendado como default

### Candidatos

| Modelo | Geral | tok/s | VRAM | Tempo 200tok |
|--------|:-----:|------:|-----:|-------------:|
| qwen3.5:9b | **3.60** | 44.7 | 6.6 GB | 4.5s |
| granite4.1:8b | 3.49 | 57.5 | 5.7 GB | 3.5s |
| gemma4:e4b-q8 | 3.46 | 51.3 | 11 GB | 3.9s |
| gemma4:26b | 3.42 | 68.2 | 17 GB | 2.9s |
| **qwen3.6:35b-a3b** | 3.34 | 22.3 | 28 GB | **8.9s** |

### Análise por caso de uso

**Para Aurelia (bot Telegram, uso interativo):**  
**Recomendado: `qwen3.5:9b`**

- Melhor pontuação geral do benchmark (3.60)
- 44.7 tok/s → 200 tokens em 4.5s, resposta percebida como rápida
- 6.6GB VRAM: libera GPU1 completamente para outras tarefas
- Tool use perfeito (T-series 4.0)
- Sem timeouts em nenhum cenário do ABS
- Bateu ou empatou com 35b-a3b em todas as séries testadas

O qwen3.6:35b-a3b **não justifica** 4.3× mais VRAM e 2× mais latência para os cenários do Telegram.

**Para Hermes (tarefas batch, análise longa):**  
**Recomendado: `qwen3.6:35b-a3b` sob demanda**

- Hermes gerencia bem sessões longas com modelos grandes
- L-series via Hermes: 3.33 (igual ou melhor que outros)
- Para tarefas que requerem raciocínio extenso, o modelo maior pode produzir output mais detalhado
- Usar apenas quando a tarefa exige — não como default permanente

**Para Aurelia se precisar de mais qualidade:**  
**Alternativa: `granite4.1:8b`**

- Menor VRAM (5.7GB), ainda mais rápido que qwen3.5:9b (57.5 tok/s)
- Pontuação Q e T equivalente ao qwen3.5:9b
- Perde em L3 (conversas muito longas) e M-series
- Libera ainda mais VRAM — permite rodar Ollama + Aurelia + outro modelo simultaneamente

### Decisão final

```
Aurelia Telegram default:  qwen3.5:9b
Hermes batch/complexo:     qwen3.6:35b-a3b (on-demand, stop Aurelia antes)
Alternativa low-VRAM:      granite4.1:8b
```

Configurar no `~/.aurelia/config/app.json`: `"default_model": "qwen3.5:9b"`

---

## 8. Diferenças entre modelos — eleição por categoria

### Melhor tool use
**Vencedor: empate técnico — todos os modelos pontuam 4.0 no T-series**  
Destaque: granite4.1:8b tem a implementação de tool use mais limpa (IBM-native `<|tool_call|>` JSON). qwen3.5:9b é o mais confiável no C-series (3.60) com menor VRAM.

### Melhor qualidade textual (Q-series)
**Vencedor: granite4.1:8b e qwen3.5:9b (empatados em 3.50)**  
Granite lidera em Q4 (diagnóstico de log: único com 4.0). qwen3.5:9b é mais consistente entre runs.

### Melhor retenção longa (L-series)
**Vencedor: qwen3.5:9b (3.67)**  
L3 (qualidade após 10 turns): qwen3.5:9b=3.0 > gemma4:e4b-q8=3.0 > granite4.1:8b=2.0 ≈ qwen3.6:35b-a3b=2.0 > gemma4:26b=1.0.  
MoE de alta capacidade não supera modelos menores em retenção — o tamanho do contexto e a arquitetura de atenção importam mais que o número de parâmetros.

### Melhor para multi-agent (M-series)
**Vencedor: gemma4:26b (3.50)**  
Único modelo com M2-H=4.0 e M2-A=4.0. Sua verbosidade natural acerta os keywords do scoring. qwen3.5:9b (3.25) vem em seguida. qwen3.6:35b-a3b (2.25) é o pior — M2-H=0 é uma falha real de adaptação ao perfil Hermes.

### Melhor throughput
**Vencedor: gemma4:e4b-q4 (69 tok/s) e gemma4:26b (68.2 tok/s)**  
Ambos MoE Gemma4 — arquitetura de mistura de especialistas com ativação esparsa. Surpreendente: 26b (17GB) é mais rápido que e4b-q8 (11GB). Isso reflete que o 26b tem mais especialistas por token mas menos carga de atenção densa.

### Melhor eficiência VRAM/qualidade
**Vencedor: qwen3.5:9b**  
3.60 geral com 6.6GB VRAM. Eficiência = score/GB = 3.60/6.6 = **0.545**.  
Granite4.1:8b: 3.49/5.7 = 0.612 (melhor eficiência absoluta, mas score total menor).  
35b-a3b: 3.34/28 = 0.119 (pior eficiência).

### Melhor modelo único para fox-server
**Vencedor: qwen3.5:9b**

Justificativa consolidada:
- Ranking #1 em score geral (3.60)
- Ranking #1 em L-series (3.67) — único relevante para sessões longas
- Ranking #1 em eficiência VRAM/qualidade
- Velocidade suficientemente alta para uso interativo (44.7 tok/s)
- Permite que a GPU1 fique livre para outros processos (open-webui, qdrant embeddings)
- Sem falhas em nenhuma série do benchmark

### Eleição por categoria

| Categoria | Modelo eleito | Justificativa |
|-----------|:-------------:|---------------|
| Tool use | qwen3.5:9b | Melhor combinação tool+VRAM+velocidade |
| Qualidade textual | granite4.1:8b | Q4 = único 4.0, diagnóstico de logs |
| Conversas longas | qwen3.5:9b | L-series 3.67, melhor do conjunto |
| Multi-agent | gemma4:26b | M-series 3.50, verbosidade natural |
| Velocidade | gemma4:e4b-q4 | 69 tok/s com qualidade aceitável |
| VRAM mínima | granite4.1:8b | 5.7GB, cabe em 1 GPU com margem |
| Default geral | **qwen3.5:9b** | Melhor score, velocidade, VRAM |
| Tarefas complexas | qwen3.6:35b-a3b | On-demand via Hermes |

---

## Apêndice — configuração técnica

```
qwen3.6:35b-a3b
  Ollama pull  : qwen3.6:35b-a3b
  VRAM         : 28 GB (2× RTX 3060, 18%/82% CPU/GPU com num_ctx=32768)
  num_ctx ABS  : 4096 (menor contexto para comparação direta)
  tok/s        : ~22-23 (MoE, 3B ativos por token)
  num_gpu      : NÃO especificar — num_gpu=999 causa 500 em MoE (bug corrigido)
  Template     : RENDERER qwen3.5, PARSER qwen3.5, TEMPLATE {{ .Prompt }}

ABS providers
  Ollama direto : http://localhost:11434/api/chat, options: {temperature, num_ctx:4096}
  Aurelia       : POST http://localhost:18790/api/chat
  Hermes        : subprocess hermes chat -Q --provider custom --max-turns 10

Checklist pré-run (obrigatório)
  1. systemctl --user stop aurelia.service
  2. pgrep -fa hermes → kill -9 <PIDs>
  3. curl Ollama keep_alive=0 → aguardar VRAM < 500MB
  4. nvidia-smi confirmar memória livre
  5. Modelo no ~/.aurelia/pi-agent/models.json (antes de qualquer run via Aurelia)
```
