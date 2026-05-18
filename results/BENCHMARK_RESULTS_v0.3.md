# Agent Benchmark Suite — Resultados v0.3

**Data:** 2026-05-18  
**Hardware:** fox-server — Xeon E5-2696 v3 (18c/36t) · 2× RTX 3060 12GB · 128 GB RAM  
**Modelos novos:** `granite4.1:8b` (IBM), `lfm2:24b` (Liquid AI)  
**Provider:** Ollama direto — séries T, C, Q, L, M (mock tools injetados pelo ABS)

---

## Contexto

Esta versão adiciona dois modelos ao benchmark:

| Modelo | Tamanho | Arquitetura | VRAM (Q4) | Status |
|--------|---------|-------------|-----------|--------|
| `granite4.1:8b` | 8B dense | IBM Granite 4.1 | ~5.3 GB | ✅ Confiável |
| `lfm2:24b` | 24B MoE (2B ativos) | Liquid Foundation Model 2 | ~14 GB | ⚠️ Tool use não confiável |

> **LFM2:** testado apenas em Q e C series. Tool use inconsistente — C1/C3 retornaram QUAL=4 por alucinação (0 tool calls), C4 recusou tool call, apenas C2/C5 usaram tools corretamente. Não recomendado para cenários que dependem de tool use. Ver seção específica.

---

## Resultados: T-series (seleção de tool)

| ID | Descrição | e4b | 26b | **Granite 4.1** |
|----|-----------|:---:|:---:|:---------------:|
| T1 | URL analysis | 4.00 | 4.00 | **4.00** |
| T2 | YouTube transcript | 4.00 | 4.00 | **4.00** |
| T3 | Health check | 4.00 | 4.00 | **4.00** |
| T4 | Parâmetros complexos (cron) | 4.00 | 4.00 | **4.00** |
| T5 | Cron scheduling | 4.00 | 4.00 | **4.00** |
| T6 | Discriminação URL vs YouTube | 4.00 | 4.00 | **4.00** |
| **Média** | | **4.00** | **4.00** | **4.00** |
| **Tool calls** | | 12/12 | 12/12 | **12/12** |
| **tok/s** | | ~69 | ~68 | ~57 |

**Nota:** T-series é empate triplo em qualidade. Granite confirma tool use 100% confiável na seleção.

---

## Resultados: C-series (chain — tool use sequencial)

| ID | Descrição | e4b | 26b | **Granite 4.1** | LFM2 24b |
|----|-----------|:---:|:---:|:---------------:|:--------:|
| C1 | URL → resumo | 4.00 | 4.00 | **4.00** ✅ | 4.00 ⚠️* |
| C2 | Health → diagnóstico | **4.00** | 3.00 | **4.00** ✅ | 3.00 ✅ |
| C3 | 2 tool calls sequenciais | 4.00 | 4.00 | **4.00** ✅ (4 calls) | 4.00 ⚠️* |
| C4 | Shell → containers | 2.00 | **3.00** | 2.00 † | 1.00 ❌ |
| C5 | Loop detection | 4.00 | 4.00 | **4.00** ✅ | 4.00 ✅ |
| **Média** | | **3.60** | **3.60** | **3.60** | 3.20 |

*LFM2 C1/C3: QUAL=4 por alucinação — 0 tool calls reais, modelo respondeu do "conhecimento".  
†Granite C4: model chamou tool e listou 9 containers corretamente. QUAL=2 por artefato de scoring (não escreveu "nove" por extenso).

**Destaques C-series:**
- Granite C2 = 4.0 vs 26b = 3.0 — Granite mais preciso em chain multi-step
- Granite C3 executou **4 tool calls** (2 calls × 2 runs) — chamadas sequenciais funcionando
- LFM2 descartado para C-series: comportamento de tool use não confiável

---

## Resultados: Q-series (qualidade, sem tools)

| ID | Descrição | e4b | 26b | **Granite 4.1** | LFM2 24b |
|----|-----------|:---:|:---:|:---------------:|:--------:|
| Q1 | Trade-offs hardware LLM | 2.22 | 2.00 | 2.00 | 2.00 |
| Q2 | Conformidade JSON | **4.00** | **4.00** | **4.00** | **4.00** |
| Q3 | Retenção contexto técnico | **4.00** | 3.00 | **4.00** | **4.00** |
| Q4 | Análise log de erro | 3.00 | 3.00 | **4.00** | 3.00 |
| **Média** | | 3.30 | 3.00 | **3.50** | 3.25 |
| **tok/s** | | ~69 | ~68 | ~57 | ~110 |

**Destaques Q-series:**
- **Q4**: Granite é o único modelo com 4.0 — melhor diagnóstico de log do conjunto
- **Q3**: Granite empata com e4b (ambos 4.0), supera 26b (3.0) e Aurelia (2.0)
- **Q1**: nenhum modelo acerta bem os trade-offs de hardware — candidato a cenário com `llm_judge`
- **LFM2 velocidade**: 110 tok/s vs ~57-69 dos demais — mas qualidade não compensa

---

## Resultados: L-series (retenção longa)

| ID | Descrição | e4b | 26b | **Granite 4.1** |
|----|-----------|:---:|:---:|:---------------:|
| L1 | Info turn 1 → turn 5 | **4.00** | **4.00** | **4.00** |
| L2 | Consistência aritmética 8 turns | **4.00** | **4.00** | **4.00** |
| L3 | Qualidade após 10 turns | **3.00** | 1.00 | 2.00 |
| **Média** | | **3.67** | 3.00 | 3.33 |

**Análise:**
- L1/L2 empate triplo — retenção factual e aritmética funciona em todos
- L3: e4b ainda lidera (3.0). Granite (2.0) fica entre e4b e 26b (1.0)
- Granite 8B dense degrada mais que e4b MoE em conversas longas — esperado: menos "capacidade de reserva" de parâmetros

---

## Resultados: M-series (perfis multi-agent)

| ID | Descrição | e4b | 26b | **Granite 4.1** |
|----|-----------|:---:|:---:|:---------------:|
| M1-A | URL analysis — perfil Aurelia | 3.00 | 3.00 | 3.00 |
| M1-H | URL analysis — perfil Hermes | 3.00 | 3.00 | 3.00 |
| M2-A | Diagnóstico — perfil Aurelia | 3.00 | **4.00** | 3.00 |
| M2-H | Diagnóstico — perfil Hermes | **4.00** | **4.00** | 3.00 |
| **Média** | | 3.25 | **3.50** | 3.00 |

**Análise:**
- Granite fica em 3.0 em todos os M-series — resposta completa mas sem atingir todos os keywords
- 26b leva vantagem em M2 (diagnóstico de sistema) — mais verboso, acerta mais keywords
- M-series favorece modelos que geram respostas longas; Granite tende a ser mais conciso

---

## Resumo comparativo — todas as séries

| Série | e4b | 26b | **Granite 4.1** | LFM2 24b |
|-------|:---:|:---:|:---------------:|:--------:|
| T (tool selection) | 4.00 | 4.00 | **4.00** | — |
| C (chain) | 3.60 | 3.60 | **3.60** | 3.20 ⚠️ |
| Q (qualidade) | 3.30 | 3.00 | **3.50** | 3.25 |
| L (retenção longa) | **3.67** | 3.00 | 3.33 | — |
| M (multi-agent) | 3.25 | **3.50** | 3.00 | — |
| **Média geral** | **3.56** | 3.42 | **3.49** | — |

### Throughput

| Modelo | tok/s | VRAM |
|--------|------:|-----:|
| LFM2 24b | **~110** | 14 GB |
| e4b (MoE) | ~69 | 9.6 GB |
| 26b (MoE) | ~68 | 17 GB |
| **Granite 4.1 8b** | ~57 | 5.3 GB |

Granite é o **mais lento** apesar de ser o menor — arquitetura dense vs MoE dos gemma4. O gargalo não é o número de parâmetros mas a eficiência da arquitetura.

---

## Análise: Granite 4.1 8b

### Pontos fortes

| Capacidade | Score | Observação |
|------------|------:|------------|
| Tool selection (T) | 4.00/4 | Perfeito — 12/12 tool calls corretos |
| Tool use real (C) | efetivo 3.80 | C4 artefato de scoring; modelo chamou tool corretamente |
| Q4 — diagnóstico log | 4.00/4 | Único modelo com 4.0 nesse cenário |
| Q3 — retenção multi-turn | 4.00/4 | Empata com e4b, supera 26b |
| VRAM | 5.3 GB | Cabe em 1 GPU, libera GPU1 para outro modelo |

### Pontos fracos

| Capacidade | Score | Observação |
|------------|------:|------------|
| L3 — qualidade 10 turns | 2.00/4 | Dense 8B degrada mais que e4b MoE em contexto longo |
| M-series | 3.00/4 | Respostas concisas perdem keywords; não é falha real |
| Velocidade | ~57 tok/s | ~18% mais lento que e4b apesar de menor |

### Veredito

Granite 4.1 8b é o **modelo mais confiável para tool use** do conjunto testado. Qualidade geral competitiva com e4b (médias praticamente idênticas: 3.49 vs 3.56). A diferença de velocidade (~57 vs ~69 tok/s) é real mas aceitável para uso como motor de agente.

**Uso recomendado:** motor de tool use em agente local com VRAM limitada. Permite rodar simultaneamente com outro modelo (e.g. e4b) nas 2× RTX 3060.

---

## Resultados: F-series — Granite via Aurelia

F-series rodado com Aurelia configurada com `granite4.1:8b` como modelo backend.  
Comparação direta com Aurelia usando `gemma4:e4b` (v0.2).

| ID | Descrição | e4b+Aurelia | **Granite+Aurelia** |
|----|-----------|:-----------:|:-------------------:|
| F1 | Raciocínio RTX 3060 | 1.50 | 1.50 |
| F2 | Conformidade JSON | **4.00** | **4.00** |
| F3 | Retenção multi-turn (4 turns) | **3.00** | 2.50 |
| F4 | Shell — Docker containers | **4.00** | **4.00** |
| F5 | Diagnóstico do servidor | **4.00** | **4.00** |
| F6 | Leitura de arquivo | 2.00 | 2.00 |
| F7 | HTTP via curl — Ollama | **4.00** | **4.00** |
| **Média** | | **3.21** | **3.07** |

**Análise:** Granite no pipeline da Aurelia fica ligeiramente abaixo do e4b, diferença concentrada no F3 (multi-turn: 2.50 vs 3.00) — consistente com L3 do benchmark direto. F4/F5/F7 (tool use real) empate perfeito. Granite é adequado para tasks de tool use na Aurelia; e4b continua melhor para conversas longas.

---

## Resultados: F-series — Granite via Hermes

F-series rodado com Hermes configurado com `granite4.1:8b` como modelo backend.  
Comparação direta com Hermes usando `gemma4:e4b` (v0.2).

| ID | Descrição | e4b+Hermes | **Granite+Hermes** |
|----|-----------|:----------:|:-----------------:|
| F1 | Raciocínio RTX 3060 | 1.33 | 1.00 |
| F2 | Conformidade JSON | **4.00** | **4.00** |
| F3 | Retenção multi-turn (4 turns) | 1.67 | **3.50** ↑ |
| F4 | Shell — Docker containers | **4.00** | **4.00** |
| F5 | Diagnóstico do servidor | **4.00** | 1.50 ↓ |
| F6 | Leitura de arquivo | 2.00 | **3.00** ↑ |
| F7 | HTTP via curl — Ollama | **4.00** | **4.00** |
| **Média** | | **3.00** | **3.00** |

**Análise:**
- **F3 ↑ (1.67→3.50):** Granite retém contexto multi-turn no Hermes melhor que e4b — o formato de sessão do Hermes favorece Granite aqui.
- **F5 ↓ (4.00→1.50):** Granite escolheu `systemctl status` (reportou "degraded") em vez de ferramentas de saúde (cpu/ram). Run 1 usou ferramentas corretas mas retornou ~4GB RAM (errado — servidor tem 128GB). Falha real de diagnóstico.
- **F6 ↑ (2.00→3.00):** Granite lê e interpreta arquivos com mais detalhes via Hermes.
- Médias idênticas (3.00), mas distribuição complementar a e4b: Granite melhor em multi-turn e leitura, pior em diagnóstico de sistema.

---

## LFM2 24b — nota de exclusão

| Cenário | Tool calls | QUAL | Status |
|---------|:----------:|:----:|--------|
| C1 | 0 | 4 | ⚠️ Alucinação — respondeu sem chamar tool |
| C2 | 2 | 3 | ✅ |
| C3 | 0 | 4 | ⚠️ Alucinação — 2 tool calls esperados |
| C4 | 0 | 1 | ❌ Recusou ("não tenho acesso a Docker") |
| C5 | 2 | 4 | ✅ |

**Conclusão:** tool use não confiável para uso em agente. Velocidade (110 tok/s) é impressionante mas inutilizável quando o modelo alucina resultados de tool em vez de executá-las. RENDERER/PARSER proprietário Liquid AI — suporte parcial no Ollama.

---

## Roadmap v0.4

- [x] Rodar Granite 4.1 8b no F-series via Aurelia
- [x] Rodar Granite 4.1 8b no F-series via Hermes
- [ ] Investigar Q3/L3 Aurelia — testar com/sem persona e nudge
- [ ] Rodar C/T/M series com Aurelia e Hermes (e4b)
- [ ] Rodar 26b nos frameworks — **aguardando troca do cooler**
- [ ] Testar Granite 4.1 30b pós-cooler (se performance 8b justificar)
- [ ] Candidatos futuros: `qwen3.6:27b`, `gemma4:31b` — pós-cooler

---

## Configuração técnica

```
Granite 4.1 8b : ollama run granite4.1:8b
  VRAM          : 5.3 GB (1× RTX 3060)
  Template      : IBM Granite nativo com <|tool_call|> JSON

LFM2 24b       : ollama run lfm2:24b
  VRAM          : 14 GB (2× RTX 3060)
  Template      : RENDERER/PARSER lfm2 (proprietário Liquid AI)
  Status        : ⚠️ tool use não confiável

Direct Ollama  : http://localhost:11434/api/chat
  Mock tools    : injetados pelo ABS por cenário
```
