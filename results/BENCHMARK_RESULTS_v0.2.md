# Agent Benchmark Suite — Resultados v0.2

**Data:** 2026-05-18  
**Hardware:** fox-server — Xeon E5-2696 v3 (18c/36t) · 2× RTX 3060 12GB · 128 GB RAM  
**Modelos:** `gemma4:e4b-it-q4_K_M` (via Ollama direto, Hermes, Aurelia)  
**Nota:** Hermes e Aurelia rodam o mesmo modelo base (`e4b`) através dos seus pipelines completos.

---

## O que foi testado

Esta versão introduz dois **providers reais de framework**:

| Provider | Mecanismo | Memória | Ferramentas |
|----------|-----------|---------|-------------|
| `ollama` (direto) | HTTP `POST /api/chat` | Nenhuma (contexto da requisição) | Mock (injetado pelo ABS) |
| `hermes` | Subprocess `hermes chat -Q` + `--resume` | Sessão CLI | Ferramentas nativas do Hermes |
| `aurelia` | HTTP `POST /api/chat` (Chat API local) | Sessão persistente (SQLite) | Ferramentas nativas da Aurelia |

Séries testadas com os frameworks: **F** (F-series, tarefas reais), **Q** (qualidade de raciocínio), **L** (retenção multi-turn longa).

---

## Resultados: F-series (tarefas reais, Hermes vs Aurelia)

Cenários desenhados para verificar capacidades reais dos frameworks: shell, leitura de arquivo, URL, multi-turn.

| ID | Descrição | Aurelia QUAL | Hermes QUAL | Aurelia ms | Hermes ms |
|----|-----------|:------------:|:-----------:|:----------:|:---------:|
| F1 | Raciocínio técnico — modelo RTX 3060 | 1.50 | 1.33 | 12.6s | 25.6s |
| F2 | Conformidade JSON | **4.00** | **4.00** | 17.6s | 23.8s |
| F3 | Retenção multi-turn (4 turns) | **3.00** | 1.67 | 32.8s | 61.8s |
| F4 | Shell — containers Docker | **4.00** | **4.00** | 13.4s | 15.9s |
| F5 | Diagnóstico saúde do servidor | **4.00** | **4.00** | 18.7s | 34.2s |
| F6 | Leitura de arquivo (`/etc/os-release`) | 2.00 | 2.00 | 5.4s | 14.2s |
| F7 | Análise de URL (fox-server dashboard) | 1.00¹ | 1.67 | 63.9s | 44.1s |

> ¹ F7 Aurelia: 1 run com timeout (120s), 1 run com resposta parcial.

**Destaques F-series:**
- **Aurelia ~40% mais rápida** que Hermes na maioria dos cenários (pipeline HTTP vs subprocess)
- **F3 (multi-turn)**: Aurelia 3.0 vs Hermes 1.67 — a sessão HTTP estável funciona melhor que o `--resume` via subprocess
- **F4/F5 empatados** em QUAL=4 — ambos executam shell corretamente
- **F6 (file read)**: ambos 2.0 — conseguem ler mas perdem metadados (kernel, arquitetura)
- **F7 (URL)**: ambos fracos — o modelo não navega adequadamente sem browser tool explícito

---

## Resultados: L-series (retenção longa, multi-turn)

O resultado mais revelador da bateria v0.2: **Hermes falha completamente** em retenção multi-turn.

| ID | Descrição | Aurelia | Hermes | Direct 26b | Direct e4b |
|----|-----------|:-------:|:------:|:----------:|:----------:|
| L1 | Info do turn 1 → perguntada no turn 5 | **4.00** | 0.00 | 4.00 | 4.00 |
| L2 | Consistência numérica em 8 turns | **4.00** | 0.00 | 4.00 | 4.00 |
| L3 | Qualidade após 10 turns | 2.00 | 2.50 | 1.00 | 2.33 |

**Análise:**
- **Hermes L1/L2 = 0**: O mecanismo `--resume` do Hermes não preserva contexto entre chamadas separadas do ABS. Cada turn envia uma nova requisição ao subprocess, e embora o `session_id` seja reutilizado, o modelo perde o histórico.
- **Aurelia L1/L2 = 4**: A sessão HTTP persistente (mapeada por `session_key → chatID`) mantém o histórico completo no SQLite da Aurelia. O pipeline funciona como esperado.
- **Direct Ollama L1/L2 = 4**: O contexto é preservado dentro da mesma janela de tokens — sem memória externa, mas sem fragmentação entre requests.
- **L3 (10 turns)**: Hermes 2.50 > Aurelia 2.00 ≈ e4b 2.33 — nenhum framework performa bem em coerência longa; o overhead de sessão da Aurelia pode estar adicionando ruído.

---

## Resultados: Q-series (qualidade, sem ferramentas)

Comparação direta entre frameworks e Ollama direto no mesmo modelo.

| ID | Descrição | Aurelia | Hermes | Direct 26b | Direct e4b |
|----|-----------|:-------:|:------:|:----------:|:----------:|
| Q1 | Trade-offs hardware LLM | 2.50 | 2.00 | 2.00 | 2.22 |
| Q2 | Formato JSON | **4.00** | **4.00** | **4.00** | **4.00** |
| Q3 | Retenção contexto técnico | 2.00 | 3.00 | 3.00 | **4.00** |
| Q4 | Análise log de erro | 3.00 | 3.00 | 3.00 | 3.00 |

**Análise Q-series:**
- **Q2 universal 4.0**: Todos os providers acertam formatação JSON — o modelo domina essa capacidade.
- **Q3 (retenção técnica)**: Direct e4b = 4.0 é melhor que Hermes/26b = 3.0 > Aurelia = 2.0. A Aurelia pode estar perdendo signal por overhead de sistema (persona, nudge, processamento de histórico).
- **Q4 (diagnóstico)**: Empate em 3.0 — tarefa de raciocínio sem multi-turn não diferencia os providers.
- **Latência Q**: Hermes 2–4× mais lento que direct Ollama para queries de texto puro. Aurelia 1.5–2× mais lenta que direct.

---

## Resumo executivo

### Por framework

| Framework | Pontos fortes | Pontos fracos |
|-----------|--------------|---------------|
| **Direct Ollama** | Mais rápido (tok/s ~69), L-series perfeita, Q3 melhor | Sem ferramentas reais, sem memória persistente |
| **Aurelia** | L-series perfeita com sessão real, ~40% mais rápido que Hermes, F3 melhor | Latência overhead ~2×, Q3 degradado |
| **Hermes** | F4/F5 correto (shell), F7 ligeiramente melhor | L1/L2 = 0 (sessão quebrada), ~2–4× mais lento |

### Por capacidade

| Capacidade | Melhor provider | Observação |
|------------|----------------|------------|
| Retenção multi-turn real | Aurelia | Hermes falha completamente em sessões separadas |
| Velocidade pura | Direct Ollama | 1s vs 10–35s dos frameworks |
| Ferramentas shell | Aurelia ≈ Hermes | Ambos acertam Docker/diagnóstico |
| Raciocínio complexo | Direct e4b | Pipeline adiciona overhead sem ganho em Q-series |
| Formato estruturado | Universal | Q2/F2 = 4.0 em todos |

---

## Latências comparativas

### F-series (Aurelia vs Hermes)

```
F3 multi-turn:  Aurelia 32.8s  ████████████░░░░░░░░░  Hermes 61.8s
F5 diagnóstico: Aurelia 18.7s  ████████░░░░░░░░░░░░░  Hermes 34.2s
F4 Docker:      Aurelia 13.4s  ██████░░░░░░░░░░░░░░░  Hermes 15.9s
F2 JSON:        Aurelia 17.6s  ████████░░░░░░░░░░░░░  Hermes 23.8s
```

### L-series (custo da memória)

```
L2 (8 turns):  Direct 2.1s  ██░  Aurelia 113s  ████████████████████░  Hermes 188s  ██████████████████████████████
L1 (5 turns):  Direct 0.9s  █░   Aurelia 55.6s ████████░              Hermes 69.7s ██████████
```

A latência da Aurelia em L-series é alta por envolver múltiplas chamadas ao pipeline completo (cada turn = 1 request HTTP completo com sessão, persona, histórico).

---

## Problemas identificados

1. **Hermes `--resume` não preserva contexto multi-turn** entre invocações separadas do ABS — L1/L2 = 0. Necessita investigação no protocolo de sessão do Hermes CLI.

2. **F7 Aurelia timeout**: A tarefa pede análise de `http://fox-server.lan/home/` — o pipeline provavelmente aguarda resposta de browser tool que não está configurada para retornar via Chat API. Timeout de 120s.

3. **Q3 Aurelia degradado** (2.0 vs e4b direct 4.0): A conversa multi-turn no Q3 pode estar sendo prejudicada pelo overhead de processamento de sessão. Investigar se a persona/nudge interferem no recall de contexto.

4. **tok/s não disponível** para frameworks (retornam `null`) — apenas o Ollama direto reporta throughput real (~68–70 tok/s).

---

## Roadmap v0.3

- [ ] Diagnosticar e corrigir sessão multi-turn do Hermes (L1/L2 = 0)
- [ ] F7: adicionar tool de browsing explícita ao cenário ou marcar como hermes-only
- [ ] Rodar e4b + 26b na F-series via Ollama direto como baseline sem framework overhead
- [ ] Adicionar `gemma4:12b` como ponto médio entre e4b e 26b
- [ ] Investigar Q3 Aurelia — comparar com/sem persona ativa
- [ ] Rodar C/T/M series com Aurelia/Hermes para comparação completa

---

## Configuração técnica

```
Aurelia Chat API : http://localhost:18790/api/chat
  Timeout        : 120s
  session_key    : abs-{scenario_id}-{run_idx}
  
Hermes CLI       : hermes chat -Q --provider custom --max-turns N [--resume session_id]
  Config         : ~/.hermes/config.yaml
  Provider       : custom (http://127.0.0.1:11434/v1)
  
Direct Ollama    : http://localhost:11434/api/chat
  Format         : tools injected by ABS mock
```
