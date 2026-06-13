# ABS — Agent Benchmark Suite

**Stage 1 of 4** in a progressive benchmark methodology for evaluating local LLMs on agentic tasks.

> **`ABS`** → `LOP` → `FORGE` → `REAL`

---

## What is ABS?

Public benchmarks (MMLU, HumanEval) measure academic capabilities. ABS measures what on-premise agents actually do: call tools correctly, retain context across turns, chain multiple operations, maintain consistency across repeated runs — all running 100% locally via Ollama.

The central premise, empirically validated across 4 stages and 19 models:

> **20% is the model, 80% is the runtime.** A well-configured 9B model outperforms a poorly-configured 30B on the tasks that matter.

ABS is the entry filter. Models that pass ABS advance to LOP (local-only pressure), then FORGE (real-world chained tasks), then REAL (browser automation + functional code verification).

---

## The Certification Funnel

ABS is not a ranking benchmark. It is the **first gate** of a progressive certification funnel.

19 models entered. Each stage is an elimination filter — not a comparison, but a capability gate. Models that can't meet the bar don't advance.

| Stage | Gate question | What it proves | Filter |
|-------|--------------|----------------|--------|
| **ABS** ← *you are here* | Can it call tools at all? | Tool mechanics, parameter accuracy, structured output | 19 entered |
| **LOP** | Does it hold under real pressure? | Consistency under operational load, no external APIs | — |
| **FORGE** | Can it function as an agent? | Multi-turn chaining, autonomous planning, deliverable output | 7 entered |
| **REAL** | Does it work in production? | Real browser, tests that pass, enterprise-grade tasks | 4 proven |
| **agent-FORGE** | *Deploy* | Production runtime for models that survived the full funnel | — |

The model that survives all 4 stages is not just "good at benchmarks" — it is **proven capable of the actual job**. agent-FORGE is where those models go to work.

---

## Benchmark Series

| Series | Focus | Scenarios | Dimensions |
|--------|-------|-----------|-----------|
| **Q** | Response quality (no tools) | Q1–Q4 | QUAL, LAT |
| **T** | Single tool use | T1–T6 | TOOL, LAT |
| **C** | Tool chaining | C1–C5 | TOOL, CHAIN, LAT |
| **L** | Long context retention | L1–L3 | CTX, QUAL |
| **M** | Multi-agent profile comparison | M1–M2 | QUAL, TOOL, LAT |

### Scoring Dimensions

| Code | What it measures | Scale |
|------|-----------------|-------|
| **QUAL** | Semantic quality of the response | 0–4 |
| **TOOL** | Tool selection and parameter accuracy | 0–4 |
| **LAT** | Total latency (lower = better) | 0–4 |
| **CTX** | Context retention across long conversations | 0–4 |

Scale 0–4 is consistent with LOP (S1–S4) for longitudinal comparison.

---

## Installation

**Requirements:** Python 3.11+, [uv](https://github.com/astral-sh/uv), Ollama running at `localhost:11434`.

```bash
git clone https://github.com/JConradoN/agent-benchmark-suite
cd agent-benchmark-suite
uv venv .venv
uv pip install -e ".[dev]"
```

---

## Usage

```bash
# Run all scenarios
.venv/bin/python run.py

# Filter by series
.venv/bin/python run.py --series T C

# Specific scenarios
.venv/bin/python run.py --scenario Q1 T3 C2

# Select model
.venv/bin/python run.py --model qwen3.5:9b

# With thinking enabled
.venv/bin/python run.py --model gemma4:26b-a4b-it-q4_K_M --think

# Runs per scenario (default: 3)
.venv/bin/python run.py --runs 5

# Summary of existing results
.venv/bin/python run.py --report

# Compare two models
.venv/bin/python compare.py \
  --models qwen3.5:9b gemma4:26b-a4b-it-q4_K_M
```

---

## Scenarios

### Q — Quality (no tools)

| ID | Name | What it tests |
|----|------|---------------|
| Q1 | Technical reasoning — LLM hardware | Reasoning about VRAM trade-offs and model selection |
| Q2 | JSON format compliance | Valid, complete JSON output without explicit format instruction |
| Q3 | Context retention — 4 turns | Recalls a numeric value mentioned in turn 1 |
| Q4 | Error log diagnosis | Identifies cause and fix from a CUDA error log |

### T — Tools (single tool)

| ID | Name | Expected tool |
|----|------|---------------|
| T1 | Selection — URL analysis | `analyze_url` |
| T2 | Selection — YouTube transcript | `youtube_transcript` |
| T3 | Selection — health check | `health_check` |
| T4 | Parameter accuracy — URL with query string | `analyze_url` (full URL preserved) |
| T5 | Selection — cron scheduling | `cron_create` with correct schedule |
| T6 | Discrimination — YouTube URL vs generic URL | `youtube_transcript` (not `analyze_url`) |

### C — Chain (multiple tools / turns)

| ID | Name | Complexity |
|----|------|------------|
| C1 | URL analysis → structured summary | 1 tool, result interpretation |
| C2 | Health check → diagnosis → recommendation | 1 tool, causal reasoning |
| C3 | 2 URL analyses → comparison | Same tool, 2 calls |
| C4 | Shell exec → interpretation | 1 tool, stdout parsing |
| C5 | Loop detection | 1 tool, verifies model doesn't enter infinite loop |

### L — Long context

| ID | Name | Turns |
|----|------|-------|
| L1 | Info in turn 1, question in turn 7 | 7 |
| L2 | Accumulated arithmetic consistency | 8 |
| L3 | Output quality after long conversation | 10 |

### M — Multi-agent profile comparison

Same scenario executed with two different agent profiles (different tool sets). Measures whether tool availability affects response quality and whether the model respects its tool constraints.

| ID | Scenario | Profile |
|----|---------|---------|
| M1-A | URL analysis + bullet summary | Profile A (web tools) |
| M1-H | Same scenario | Profile B (ops tools) |
| M2-A | Slowness diagnosis | Profile A |
| M2-H | Same scenario | Profile B |

---

## Output Format

Results written to `results/run_<ID>_<model>.jsonl`, one JSON object per run:

```json
{
  "scenario_id": "T1",
  "series": "T",
  "run_idx": 0,
  "model": "qwen3.5:9b",
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

Benchmark reports are saved as `results/BENCHMARK_RESULTS_<version>.md`.

---

## Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

12 unit tests covering scorer functions (keyword_match, json_schema, tool_call, latency).

---

## Project Structure

```
agent-benchmark-suite/
├── abs/
│   ├── config.py              # RunConfig, ProviderConfig
│   ├── scenario.py            # Scenario, Turn, ToolDef, ScoreSpec
│   ├── runner.py              # BenchmarkRunner with tool call loop
│   ├── scorer.py              # Scoring functions by method
│   ├── reporter.py            # Summary table (rich)
│   ├── providers/
│   │   ├── base.py            # Provider protocol
│   │   ├── ollama.py          # Ollama provider (OpenAI-compatible, mock tools)
│   │   └── ...                # Additional agent framework providers
│   └── framework_runner.py    # FrameworkRunner (real tools, no mocks)
├── scenarios/
│   ├── tools.py               # ToolDef collections per agent profile
│   ├── q_series.py            # Q1–Q4
│   ├── t_series.py            # T1–T6
│   ├── c_series.py            # C1–C5
│   ├── l_series.py            # L1–L3
│   ├── m_series.py            # M1-A, M1-H, M2-A, M2-H
│   └── f_series.py            # F-series (framework-specific tasks)
├── run.py                     # Main CLI
├── compare.py                 # Model comparison
├── results/
│   ├── run_<ID>_<model>.jsonl          # Raw data per scenario/model
│   └── BENCHMARK_RESULTS_<version>.md  # Analysis reports
└── tests/
    └── test_scorer.py
```

---

## Key Findings

After running 19 models through ABS and the subsequent stages:

- **Family predicts, scale delivers.** Within a good model family (Qwen3.5, Gemma4), larger models perform better. Across families, architectural quality dominates scale.
- **Tool selection accuracy (TOOL) correlates strongly with FORGE/REAL performance.** Models that struggle with T-series scenarios don't recover at higher stages.
- **Consistency (STAB) is the hidden discriminator.** A model that scores 3.5 on a single run but varies ±1.5 across 5 runs is not production-viable.
- **Thinking mode helps some models on Q-series, hurts latency, neutral on T-series.**

---

## Related

- **[LOP](https://github.com/JConradoN/LOP)** — Stage 2: local-only pressure (S1–S4)
- **[FORGE](https://github.com/JConradoN/FORGE)** — Stage 3: real-world chained tasks
- **[REAL](https://github.com/JConradoN/REAL)** — Stage 4: browser automation + functional code
- **[agent-FORGE](https://github.com/JConradoN/agent-FORGE)** — the framework that emerged from this research
- **[Conrado Nogueira](https://github.com/JConradoN/Conrado-Nogueira)** — full profile and project index

---

*Hardware: fox-server — Xeon E5-2696v3 · 128 GB ECC · 2× RTX 3060 12 GB. All inference local, no cloud.*
