#!/usr/bin/env bash
# ================================================================
# run_bateria_16k.sh — Bateria Final de 17 Modelos
#
# Tier 1 (12 modelos, Single GPU ≤10 GB):
#   gemma4:e4b, gemma4-12b-unsloth, qwen3.5:9b, qwen3:8b, qwen3:14b,
#   phi4:14b, lfm2.5:8b, rnj-1:8b, ministral-3:8b, ministral-3:14b,
#   granite4.1:3b, granite4.1:8b
#
# Tier 2 (5 modelos, Dual GPU 10-20 GB):
#   gemma4:26b, qwen3.6:27b, lfm2:24b-a2b, devstral-small-2:24b,
#   granite4.1:30b
#
# Fase 1: ABS direct (T C Q L M, 3 runs)
#   Qwen3 family: --no-think-prefix (qwen3.x:* tem thinking leakage)
#   Warmup: cada modelo é aquecido via API antes de medir
#
# Fase 2: llms-on-prem S1→S4
#   S1: bash scripts/run-s1-benchmark.sh  (K=5)
#   S2-S4: python3 scripts/run-sN-benchmark.py
#   Warmup: modelo aquecido antes de S1 de cada modelo
#
# Resume: por CENÁRIO no ABS (não por modelo) — evita re-runs com append
#   duplicado. Por marker de arquivo no LOP (run5.txt / summary.md).
#
# Uso:
#   nohup bash run_bateria_16k.sh 2>&1 | tee ~/bateria_$(date +%Y%m%d_%H%M).log &
# ================================================================

set -uo pipefail

ABS_DIR="/home/conrado/repos/estudo/agent-benchmark-suite"
LOP_DIR="/home/conrado/repos/estudo/llms-on-prem"
TIMEOUT=600
RUNS=3

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ── Cria alias para HF model (evita barras nos paths de saída) ───────────────
# hf.co/unsloth/gemma-4-12B-it-GGUF:Q4_K_M → gemma4-12b-unsloth:q4km
# Operação instantânea — aponta para os mesmos blobs, sem cópia de dados.
log "Criando alias gemma4-12b-unsloth:q4km para HF model..."
docker exec ollama ollama cp \
    "hf.co/unsloth/gemma-4-12B-it-GGUF:Q4_K_M" \
    "gemma4-12b-unsloth:q4km" 2>/dev/null \
    && log "  alias criado" \
    || log "  alias já existe (ok)"

# ── Modelos ──────────────────────────────────────────────────────────────────
TIER1=(
    "gemma4:e4b-it-q4_K_M"
    "gemma4-12b-unsloth:q4km"
    "qwen3.5:9b"
    "qwen3:8b"
    "qwen3:14b"
    "phi4:14b"
    "lfm2.5:8b"
    "rnj-1:8b"
    "ministral-3:8b"
    "ministral-3:14b"
    "granite4.1:3b"
    "granite4.1:8b"
)

TIER2=(
    "gemma4:26b"
    "qwen3.6:27b"
    "lfm2:24b-a2b"
    "devstral-small-2:24b"
    "granite4.1:30b"
)

# ── Família Qwen3: precisa de --no-think-prefix ───────────────────────────────
is_qwen3() {
    case "$1" in
        qwen3:* | qwen3.*:*) return 0 ;;
        *) return 1 ;;
    esac
}

# ── Modelos sem suporte a tool calling via Ollama API ─────────────────────────
# phi4:14b retorna HTTP 400 "does not support tools" em qualquer cenário com tools.
# Nesses casos rodar apenas L (latência, sem tools) e Q (QA, sem tools) = 8 cenários.
no_tools_model() {
    case "$1" in
        phi4:14b) return 0 ;;
        *) return 1 ;;
    esac
}

# ── Aguarda modelo estar disponível no Ollama ─────────────────────────────────
wait_for_model() {
    local model="$1"
    local n=0
    # Usa REST API em vez de docker exec — funciona em qualquer contexto (nohup, cron, etc.)
    while ! curl -s http://localhost:11434/api/tags | grep -qF "\"$model\""; do
        n=$((n + 1))
        log "  aguardando pull [$n]: $model (60s)"
        sleep 60
    done
    log "  modelo disponível: $model"
}

# ── Nome seguro para diretório (igual ao runner.py para jsonl) ───────────────
safe_tag() { echo "$1" | sed 's|[:/]|_|g'; }          # para outdir
model_safe() { echo "$1" | tr ':/' '__'; }             # para nome do jsonl (runner usa replace(':', '_').replace('/', '_'))

# ── Warmup: carrega modelo em VRAM e aquece KV cache ─────────────────────────
# Sem warmup, o run 1 de cada modelo tem latência inflada (carregamento inicial
# + KV cache frio). Bloqueia até a resposta chegar — modelo garantido quente.
warmup_model() {
    local model="$1"
    log "  Warmup: $model"
    curl -s http://localhost:11434/api/chat \
        -d "{\"model\":\"$model\",\"stream\":false,
             \"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],
             \"options\":{\"num_predict\":3}}" \
        > /dev/null
    log "  Warmup OK: $model"
}

# ── Fase 1: ABS direct — resume por CENÁRIO ──────────────────────────────────
# Resume por cenário (não por modelo) para evitar append duplicado:
# se o batch cair com 15/22 cenários feitos, re-rodaria tudo com --series
# (append mode do runner dobraria os runs dos 15 já completos).
# Solução: verificar cada jsonl individualmente e passar só os incompletos
# via --scenario.
run_abs() {
    local model="$1"
    local tag ms outdir
    tag=$(safe_tag "$model")
    ms=$(model_safe "$model")
    outdir="$ABS_DIR/results/bateria_16k/${tag}"
    mkdir -p "$outdir"

    # Modelos sem tool calling só podem rodar L (sem tools) e Q (sem tools)
    local all_scenarios
    if no_tools_model "$model"; then
        all_scenarios=(Q1 Q2 Q2v2 Q3 Q4 L1 L2 L3)
        log "  phi4 no-tools: rodando só Q+L (8 cenários)"
    else
        all_scenarios=(T1 T2 T3 T4 T5 T6 C1 C2 C3 C4 C5 Q1 Q2 Q2v2 Q3 Q4 L1 L2 L3 M1-A M1-H M2-A M2-H)
    fi
    local incomplete=()
    for sc in "${all_scenarios[@]}"; do
        local f="$outdir/run_${sc}_${ms}.jsonl"
        if [[ ! -f "$f" ]] || [[ $(wc -l < "$f") -lt $RUNS ]]; then
            incomplete+=("$sc")
        fi
    done

    if [[ ${#incomplete[@]} -eq 0 ]]; then
        log "  ABS skip (todos 22 cenários completos): $model"
        return 0
    fi

    log "  ABS start: $model — ${#incomplete[@]}/23 cenários pendentes: ${incomplete[*]}"
    warmup_model "$model"
    cd "$ABS_DIR"

    local extra=""
    is_qwen3 "$model" && extra="--no-think-prefix"

    # shellcheck disable=SC2086
    python3 run.py \
        --num-ctx 16384 \
        --provider   ollama \
        --model      "$model" \
        --scenario   "${incomplete[@]}" \
        --runs       "$RUNS" \
        --timeout    "$TIMEOUT" \
        --output-dir "$outdir" \
        $extra \
        && log "  ABS OK: $model" \
        || log "  ABS FALHOU (continuando): $model"
}

# ── Fase 2: llms-on-prem S1–S4 ───────────────────────────────────────────────
run_lop() {
    local model="$1"
    local today
    today=$(date +%Y-%m-%d)
    # Mesma sanitização do Python: : → -  / → _
    local safe
    safe=$(echo "$model" | sed 's|:|−|g; s|/|_|g')
    # (usa traço unicode U+2212 no sed acima? Não — usar traço ASCII)
    safe=$(echo "$model" | tr ':' '-' | tr '/' '_')

    cd "$LOP_DIR"

    # S1 (shell script, K=5) — warmup antes do primeiro run
    local s1_marker="results/benchmarks/S1-${safe}-${today}-run5.txt"
    if [[ -f "$s1_marker" ]]; then
        log "  LOP S1 skip: $model"
    else
        log "  LOP S1 start: $model"
        warmup_model "$model"
        bash scripts/run-s1-benchmark.sh "$model" \
            && log "  LOP S1 OK: $model" \
            || log "  LOP S1 FALHOU (continuando): $model"
    fi

    # S2, S3, S4 (Python, summary como marker de conclusão)
    for n in 2 3 4; do
        local marker="results/benchmarks/S${n}-${safe}-${today}-summary.md"
        if [[ -f "$marker" ]]; then
            log "  LOP S${n} skip: $model"
            continue
        fi
        log "  LOP S${n} start: $model"
        python3 "scripts/run-s${n}-benchmark.py" "$model" \
            && log "  LOP S${n} OK: $model" \
            || log "  LOP S${n} FALHOU (continuando): $model"
    done
}

# ════════════════════════════════════════════════════════════════════════════
# FASE 1 — ABS direct
# ════════════════════════════════════════════════════════════════════════════
log "════════════════════════════════════════════════════"
log "FASE 1 — ABS direct (T/C/Q/L/M, runs=${RUNS})"
log "════════════════════════════════════════════════════"

for model in "${TIER1[@]}"; do
    log "── [ABS Tier1] $model"
    run_abs "$model"
done

for model in "${TIER2[@]}"; do
    log "── [ABS Tier2] $model"
    wait_for_model "$model"
    run_abs "$model"
done

# ════════════════════════════════════════════════════════════════════════════
log "════════════════════════════════════════════════════"
log "H_context_A CONCLUÍDO — ABS num_ctx=16384"
log "  Resultados → $ABS_DIR/results/bateria_16k/"
log "════════════════════════════════════════════════════"
