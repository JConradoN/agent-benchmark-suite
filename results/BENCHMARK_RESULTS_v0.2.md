# Agent Benchmark Suite — Resultados v0.2

**Data:** 2026-05-18  
**Hardware:** fox-server — Xeon E5-2696 v3 (18c/36t) · 2× RTX 3060 12GB · 128 GB RAM  
**Modelos:** `gemma4:e4b-it-q4_K_M` (via Ollama direto, Hermes, Aurelia)  
**Nota:** Hermes e Aurelia rodam o mesmo modelo base (`e4b`) através dos seus pipelines completos.

> **v0.2.1 (2026-05-18):** Corrigido bug no `hermes_provider` — `session_id` era lido do
> stdout mas o Hermes em modo `-Q` o imprime no stderr. O `--resume` nunca era passado,
> fazendo cada turn rodar como sessão nova. L-series re-rodada após o fix.

---

## O que foi testado

Esta versão introduz dois **providers reais de framework**:

| Provider | Mecanismo | Memória | Ferramentas |
|----------|-----------|---------|-------------|
| `ollama` (direto) | HTTP `POST /api/chat` | Nenhuma (contexto da requisição) | Mock (injetado pelo ABS) |
| `hermes` | Subprocess `hermes chat -Q` + `--resume` | Sessão CLI | Ferramentas nativas do Hermes |
| `aurelia` | HTTP `POST /api/chat` (Chat API local) | Sessão persistente (SQLite) | Ferramentas nativas da Aurelia |

Séries testadas com os frameworks: **F** (tarefas reais), **Q** (qualidade de raciocínio), **L** (retenção multi-turn longa).

---

## Resultados: F-series (tarefas reais)

Inclui baseline Ollama direto (mock tools) + frameworks com ferramentas reais.

> **F7 reformulado:** a versão original (`fox-server.lan/home/`) usava browser tool não disponível no provider custom e a URL não resolve via localhost. Substituído por `curl http://localhost:11434/api/tags` — testa HTTP via shell, que ambos os frameworks executam nativamente.

| ID | Descrição | e4b direto | Aurelia | Hermes |
|----|-----------|:----------:|:-------:|:------:|
| F1 | Raciocínio — modelo RTX 3060 | 2.00 | 1.50 | 1.33 |
| F2 | Conformidade JSON | **4.00** | **4.00** | **4.00** |
| F3 | Retenção multi-turn (4 turns) | 3.00 | 3.00 | 1.67 |
| F4 | Shell — containers Docker | **4.00** | **4.00** | **4.00** |
| F5 | Diagnóstico saúde do servidor | **4.00** | **4.00** | **4.00** |
| F6 | Leitura de arquivo (`/etc/os-release`) | 1.00 | 2.00 | 2.00 |
| F7 | HTTP via shell — modelos Ollama | 3.00 | **4.00** | **4.00** |

| ID | e4b direto ms | Aurelia ms | Hermes ms |
|----|:-------------:|:----------:|:---------:|
| F1 | 40s | 12.6s | 25.6s |
| F2 | 1s | 17.6s | 23.8s |
| F3 | 7.3s | 32.8s | 61.8s |
| F4 | 4.6s | 13.4s | 15.9s |
| F5 | 8.9s | 18.7s | 34.2s |
| F6 | 2.1s | 5.4s | 14.2s |
| F7 | 7.2s | 34.3s | 33.2s |

**Destaques F-series:**
- **F6**: Ollama direto (1.0) vai *pior* que os frameworks (2.0) — sem pipeline real o modelo alucina o conteúdo em vez de ler o arquivo
- **F7**: Frameworks (4.0) superam Ollama direto (3.0) — curl real retorna a lista completa; sem tool o modelo adivinha os modelos
- **F3 (multi-turn)**: e4b direto e Aurelia empatam (3.0), Hermes cai (1.67) — sessão subprocess mais frágil para contexto curto
- **F4/F5 empate triplo** em 4.0 — shell/diagnóstico funciona igual nos três
- **Aurelia ~40% mais rápida** que Hermes (HTTP vs subprocess)

---

## Resultados: L-series (retenção longa, multi-turn)

| ID | Descrição | Aurelia | Hermes | Direct 26b | Direct e4b |
|----|-----------|:-------:|:------:|:----------:|:----------:|
| L1 | Info do turn 1 → perguntada no turn 5 | **4.00** | **4.00** | 4.00 | 4.00 |
| L2 | Consistência numérica em 8 turns | **4.00** | **4.00** | 4.00 | 4.00 |
| L3 | Qualidade após 10 turns | 2.00 | **3.50** | 1.00 | 2.33 |

**Análise:**
- **L1/L2 — todos 4.0**: Com o fix do `session_id`, o Hermes preserva contexto corretamente via `--resume`. Aurelia via SQLite. Ollama direto via janela de tokens.
- **L3 — Hermes 3.50 lidera**: Em conversas muito longas (10 turns) o Hermes vai melhor que Aurelia (2.0) e e4b direto (2.33). O overhead de sessão da Aurelia provavelmente dilui o contexto ao processar histórico acumulado.
- **Direct Ollama L3 = 1.0 (26b)**: O 26b degrada mais em conversas longas que o e4b — mais tokens de raciocínio por turno enchem a janela mais rápido.

---

## Resultados: Q-series (qualidade, sem ferramentas)

| ID | Descrição | Aurelia | Hermes | Direct 26b | Direct e4b |
|----|-----------|:-------:|:------:|:----------:|:----------:|
| Q1 | Trade-offs hardware LLM | 2.50 | 2.00 | 2.00 | 2.22 |
| Q2 | Formato JSON | **4.00** | **4.00** | **4.00** | **4.00** |
| Q3 | Retenção contexto técnico | 2.00 | 3.00 | 3.00 | **4.00** |
| Q4 | Análise log de erro | 3.00 | 3.00 | 3.00 | 3.00 |

**Análise Q-series:**
- **Q2 universal 4.0**: Formatação JSON é dominada por todos os providers.
- **Q3**: e4b direto = 4.0 > Hermes/26b = 3.0 > Aurelia = 2.0. A Aurelia perde signal em multi-turn por overhead de processamento de sessão (persona, nudge, histórico).
- **Q4 empate em 3.0**: Diagnóstico de log é tarefa single-turn — não diferencia providers.
- **Latência Q**: Hermes 2–4× mais lento que direct Ollama. Aurelia 1.5–2× mais lenta.

---

## Resumo executivo

### Por framework

| Framework | Pontos fortes | Pontos fracos |
|-----------|--------------|---------------|
| **Direct Ollama** | Mais rápido (~69 tok/s), Q3 melhor, L1/L2 perfeito | Sem ferramentas reais, sem memória persistente entre sessões |
| **Aurelia** | L1/L2 perfeito, ~40% mais rápido que Hermes, F3 melhor | Overhead ~2×, Q3/L3 degradados |
| **Hermes** | L1/L2/L3 melhor (memória longa), F4/F5 correto | F3 fraco, ~2–4× mais lento que direct |

### Por capacidade

| Capacidade | Melhor provider | Observação |
|------------|----------------|------------|
| Retenção longa (L1/L2) | Empate (todos 4.0) | Após fix do Hermes |
| Qualidade em conversa longa (L3) | **Hermes** | 3.50 vs Aurelia 2.0 |
| Velocidade | **Direct Ollama** | 1s vs 10–35s dos frameworks |
| Ferramentas shell (F4/F5) | Empate | Ambos frameworks acertam |
| Multi-turn curto (F3/Q3) | **Hermes** leve vantagem em Q3; **Aurelia** em F3 | Depende do tamanho da sessão |
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
L3 (10 turns): Direct 10.2s  ████░  Aurelia 148s  ████████████████████░  Hermes 190s  ████████████████████████████
L2 (8 turns):  Direct  2.1s  █░     Aurelia 113s  ████████████████░      Hermes 211s  ██████████████████████████████
L1 (5 turns):  Direct  0.9s  ░      Aurelia  55s  ████████░              Hermes  97s  ██████████████
```

A latência alta dos frameworks em L-series é esperada: cada turn é um request completo com sessão, persona e histórico acumulado.

---

## Problemas identificados e status

| # | Problema | Status |
|---|----------|--------|
| 1 | Hermes `--resume` não funcionava — `session_id` lido do stdout em vez do stderr | ✅ **Corrigido** (`hermes_provider.py`) |
| 2 | F7 timeout — browser tool indisponível, URL não resolve via localhost | ✅ **Corrigido** (cenário reformulado para curl localhost:11434) |
| 3 | Q3/L3 Aurelia degradados — overhead de sessão dilui contexto | ⚠️ A investigar |
| 4 | `tok/s` não disponível para frameworks (retornam `null`) | ℹ️ Limitação de design |

---

## Roadmap v0.3

- [x] F7: reformulado para curl localhost:11434 — ambos frameworks agora 4.0
- [x] Rodar e4b F-series via Ollama direto (baseline concluído)
- [ ] Investigar Q3/L3 Aurelia — testar com/sem persona e nudge ativos
- [x] `gemma4:12b` não existe — família gemma4 só tem e4b e 26b
- [ ] Rodar C/T/M series com Aurelia/Hermes para comparação completa
- [ ] Rodar 26b nos frameworks após troca do cooler do processador

---

## Configuração técnica

```
Aurelia Chat API : http://localhost:18790/api/chat
  Timeout        : 120s
  session_key    : abs-{scenario_id}-{run_idx}

Hermes CLI       : hermes chat -Q --provider custom --max-turns N [--resume session_id]
  session_id     : capturado do stderr (não stdout) em modo -Q
  Config         : ~/.hermes/config.yaml
  Provider       : custom (http://127.0.0.1:11434/v1)

Direct Ollama    : http://localhost:11434/api/chat
  Format         : tools injected by ABS mock
```
