# Agent Benchmark Suite (ABS)

Benchmark estruturado para avaliar modelos LLM no contexto real de agentes de IA locais.

Desenvolvido para medir o que importa na prática: qualidade de resposta, uso correto de tools, latência end-to-end, retenção de contexto em conversas longas e comportamento multi-agente — tudo rodando 100% local via Ollama.

---

## Motivação

Benchmarks públicos (MMLU, HumanEval, etc.) medem capacidades acadêmicas. O ABS mede o que agentes como **Aurelia** e **Hermes** realmente fazem no dia a dia: analisar URLs, transcrever vídeos, verificar saúde do servidor, agendar tarefas, encadear múltiplas ferramentas.

A premissa central, validada empiricamente: **o gargalo em agentes locais não é o tamanho do modelo — é a qualidade da estrutura ao redor dele.** Um modelo de 9.7B bem configurado supera modelos de 30B mal configurados nos cenários que importam.

---

## Séries de benchmark

| Série | Foco | Cenários | Dimensões |
|-------|------|----------|-----------|
| **Q** | Qualidade de resposta (sem tools) | Q1–Q4 | QUAL, LAT |
| **T** | Uso de tool único | T1–T6 | TOOL, LAT |
| **C** | Encadeamento de tools | C1–C5 | TOOL, CHAIN, LAT |
| **L** | Contexto longo e retenção | L1–L3 | CTX, QUAL |
| **M** | Multi-agente (Aurelia vs Hermes) | M1–M2 | QUAL, TOOL, LAT |

### Dimensões de pontuação

| Código | O que mede | Escala |
|--------|------------|--------|
| **QUAL** | Qualidade semântica da resposta | 0–4 |
| **TOOL** | Seleção e parametrização correta de tool | 0–4 |
| **LAT** | Latência total (menor = melhor) | 0–4 |
| **CTX** | Retenção de contexto em conversas longas | 0–4 |

Escala 0–4 consistente com os benchmarks S1–S4 do projeto `llms-on-prem`.

---

## Instalação

**Pré-requisitos:** Python 3.11+, [uv](https://github.com/astral-sh/uv), Ollama rodando em `localhost:11434`.

```bash
git clone https://github.com/jconrado/agent-benchmark-suite
cd agent-benchmark-suite
uv venv .venv
uv pip install -e ".[dev]"
```

---

## Uso

### Rodar todos os cenários

```bash
.venv/bin/python run.py
```

### Filtrar por série ou cenário específico

```bash
# Só as séries T (tools) e C (chain)
.venv/bin/python run.py --series T C

# Cenários específicos
.venv/bin/python run.py --scenario Q1 T3 C2
```

### Trocar modelo

```bash
# Modelo padrão (e4b)
.venv/bin/python run.py --model gemma4:e4b-it-q4_K_M

# Modelo grande
.venv/bin/python run.py --model gemma4:26b-a4b-it-q4_K_M

# Com thinking habilitado
.venv/bin/python run.py --model gemma4:26b-a4b-it-q4_K_M --think
```

### Número de runs por cenário

```bash
# 5 runs por cenário (padrão: 3)
.venv/bin/python run.py --runs 5
```

### Ver resumo de resultados existentes

```bash
.venv/bin/python run.py --report
```

### Comparar dois modelos

```bash
.venv/bin/python compare.py \
  --models gemma4:e4b-it-q4_K_M gemma4:26b-a4b-it-q4_K_M

# Filtrar por série
.venv/bin/python compare.py \
  --models gemma4:e4b-it-q4_K_M gemma4:26b-a4b-it-q4_K_M \
  --series T C
```

---

## Cenários

### Q — Quality (sem tools)

| ID | Nome | O que testa |
|----|------|-------------|
| Q1 | Raciocínio técnico — hardware LLM | Raciocínio sobre trade-offs de VRAM e modelos |
| Q2 | Conformidade de formato JSON | Saída JSON válida e completa sem instrução de formato |
| Q3 | Retenção de contexto — 4 turns | Lembra de dado numérico mencionado no turn 1 |
| Q4 | Diagnóstico de log de erro | Identifica causa e solução a partir de log CUDA |

### T — Tools (single tool)

| ID | Nome | Tool esperada |
|----|------|---------------|
| T1 | Seleção — URL analysis | `analyze_url` |
| T2 | Seleção — YouTube transcript | `youtube_transcript` |
| T3 | Seleção — health check | `health_check` |
| T4 | Precisão de parâmetro — URL com query string | `analyze_url` (URL completa) |
| T5 | Seleção — cron scheduling (Hermes) | `cron_create` com schedule correto |
| T6 | Discriminação — URL YouTube vs URL genérica | `youtube_transcript` (não `analyze_url`) |

### C — Chain (múltiplas tools / turns)

| ID | Nome | Complexidade |
|----|------|-------------|
| C1 | URL analysis → resumo estruturado | 1 tool, interpretação do resultado |
| C2 | Health check → diagnóstico → recomendação | 1 tool, raciocínio causal |
| C3 | 2 análises de URL → comparação | Mesma tool, 2 chamadas |
| C4 | Shell exec → interpretação (Hermes) | 1 tool, parsing de stdout |
| C5 | Loop detection | 1 tool, verifica que não entra em loop |

### L — Long context

| ID | Nome | Turns |
|----|------|-------|
| L1 | Info no turn 1, pergunta no turn 7 | 7 |
| L2 | Aritmética acumulativa consistente | 8 |
| L3 | Qualidade após conversa longa | 10 |

### M — Multi-agent

Mesmo cenário executado com perfil Aurelia (tools: health, URL, YouTube) e perfil Hermes (tools: health, shell, file, cron, URL). Compara qual perfil/tool-set produz melhor resultado.

| ID | Cenário | Perfil |
|----|---------|--------|
| M1-A | URL analysis + resumo em bullets | Aurelia |
| M1-H | Mesmo cenário | Hermes |
| M2-A | Diagnóstico de lentidão | Aurelia |
| M2-H | Mesmo cenário | Hermes |

---

## Saída e resultados

### Arquivos de run

Resultados gravados em `results/run_<ID>_<model>.jsonl`, uma linha JSON por run:

```json
{
  "scenario_id": "T1",
  "series": "T",
  "run_idx": 0,
  "model": "gemma4:e4b-it-q4_K_M",
  "think": false,
  "timestamp": "2026-05-18T14:00:00Z",
  "final_output": "...",
  "tool_calls": [...],
  "tool_calls_count": 1,
  "loop_exhausted": false,
  "iterations": 2,
  "latency_ms": 1842,
  "tok_per_s": 68.4,
  "scores": {"TOOL": 4, "LAT": 4}
}
```

### Relatórios de benchmark

Relatórios de análise são salvos em `results/BENCHMARK_RESULTS_<versão>.md`.

| Arquivo | Descrição | Data |
|---------|-----------|------|
| [BENCHMARK_RESULTS_v0.1.md](results/BENCHMARK_RESULTS_v0.1.md) | Ollama direto — `e4b` vs `26b`, séries Q/T/C/L/M | 2026-05-18 |
| [BENCHMARK_RESULTS_v0.2.md](results/BENCHMARK_RESULTS_v0.2.md) | Hermes + Aurelia providers — séries F/Q/L, comparação de frameworks | 2026-05-18 |

---

## Testes

```bash
.venv/bin/pytest tests/ -v
```

12 testes unitários cobrindo scorer (keyword\_match, json\_schema, tool\_call, latency).

---

## Estrutura do projeto

```
agent-benchmark-suite/
├── abs/
│   ├── config.py          # RunConfig, ProviderConfig
│   ├── scenario.py        # Scenario, Turn, ToolDef, ScoreSpec
│   ├── runner.py          # BenchmarkRunner com loop de tool calls
│   ├── scorer.py          # Funções de scoring por método
│   ├── reporter.py        # Tabela de resumo (rich)
│   ├── providers/
│   │   ├── base.py            # Protocol Provider
│   │   ├── ollama.py          # Provider Ollama (OpenAI-compatible, mock tools)
│   │   ├── hermes_provider.py # Provider Hermes (subprocess hermes chat -Q)
│   │   └── aurelia_provider.py# Provider Aurelia (HTTP Chat API :18790)
│   └── framework_runner.py    # FrameworkRunner (sem mock tools — ferramentas reais)
├── scenarios/
│   ├── tools.py           # ToolDef: AURELIA_TOOLS, HERMES_TOOLS, ALL_TOOLS
│   ├── q_series.py        # Q1–Q4
│   ├── t_series.py        # T1–T6
│   ├── c_series.py        # C1–C5
│   ├── l_series.py        # L1–L3
│   ├── m_series.py        # M1-A, M1-H, M2-A, M2-H
│   └── f_series.py        # F1–F7 (tarefas reais para frameworks)
├── run.py                 # CLI principal
├── compare.py             # Comparação entre modelos
├── results/
│   ├── run_<ID>_<model>.jsonl          # Dados brutos por cenário/modelo
│   └── BENCHMARK_RESULTS_<versão>.md  # Relatórios de análise
└── tests/
    └── test_scorer.py
```

---

## Relacionado

- [`llms-on-prem`](https://github.com/jconrado/llms-on-prem) — benchmarks S1–S4, artigo científico sobre eficiência de LLMs locais (escala 0–4 compartilhada)
- [Aurelia](https://github.com/jconrado/aurelia) — agente Telegram em Go com 3-layer memory
- [Hermes Agent](https://hermes-agent.org) — agente autônomo Python (Nous Research)
