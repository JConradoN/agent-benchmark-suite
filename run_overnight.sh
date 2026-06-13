#!/bin/bash
# Batch overnight — todos os modelos pendentes
# Executa: granite4.1:30b, gemma4:e4b-q8, qwen3.5:27b, qwen3.6:27b
# Roda direct (T/C/Q/L/M) + framework (F/Q/L via Aurelia e Hermes)

set -uo pipefail
cd /home/conrado/repos/estudo/agent-benchmark-suite

AURELIA_CONFIG=/home/conrado/.aurelia/config/app.json
HERMES_CONFIG=/home/conrado/.hermes/config.yaml
LOG=/tmp/abs_overnight.log

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

set_model() {
    local model="$1"
    python3 -c "
import json
with open('$AURELIA_CONFIG') as f: d=json.load(f)
d['default_model']='$model'
with open('$AURELIA_CONFIG','w') as f: json.dump(d,f,indent=2)
"
    sed -i "s/^  default: .*/  default: $model/" "$HERMES_CONFIG"
    systemctl --user restart aurelia.service
    sleep 10
    STATUS=$(systemctl --user is-active aurelia.service)
    log "  aurelia restart: $STATUS (model=$model)"
}

run_direct() {
    local model="$1"; shift
    log "  direct ollama: $model — séries $*"
    python3 run.py --provider ollama --model "$model" --series "$@" --runs 2 2>&1 | tee -a "$LOG"
}

run_framework() {
    local model="$1"
    local outdir="$2"
    mkdir -p "$outdir"
    log "  framework aurelia: $model"
    python3 run.py --provider aurelia --series F Q L --runs 2 --timeout 600 --output-dir "$outdir" 2>&1 | tee -a "$LOG"
    log "  framework hermes: $model"
    python3 run.py --provider hermes --model "$model" --series F Q L --runs 2 --timeout 600 --output-dir "$outdir" 2>&1 | tee -a "$LOG"
}

log "=== OVERNIGHT BATCH INICIADO ==="

# ── Aguarda qwen3.5:9b framework terminar ─────────────────────────────────────
log "Aguardando qwen3.5:9b framework completar (28 arquivos)..."
while [ "$(ls results/framework_qwen3.5_9b/*.jsonl 2>/dev/null | wc -l)" -lt 28 ]; do
    DONE=$(ls results/framework_qwen3.5_9b/*.jsonl 2>/dev/null | wc -l)
    log "  $DONE/28 prontos..."
    sleep 60
done
log "qwen3.5:9b framework completo."

# ── Aguarda downloads de 27b terminarem ───────────────────────────────────────
log "Aguardando downloads de qwen3.5:27b e qwen3.6:27b..."
while ! docker exec ollama ollama list | grep -q "qwen3.5:27b"; do
    log "  aguardando qwen3.5:27b..."; sleep 60
done
while ! docker exec ollama ollama list | grep -q "qwen3.6:27b"; do
    log "  aguardando qwen3.6:27b..."; sleep 60
done
log "Downloads completos."
docker exec ollama ollama list | grep qwen | tee -a "$LOG"

# ── FASE 0: granite4.1:8b framework (rerun com ctx 32768) ────────────────────
log "=== FASE 0: granite4.1:8b — F/Q/L framework (rerun ctx corrigido) ==="
rm -f results/framework_granite4.1_8b/*.jsonl
set_model "granite4.1:8b"
run_framework "granite4.1:8b" "results/framework_granite4.1_8b"
log "FASE 0 concluída."

# ── FASE 2: gemma4:e4b-q8 framework ──────────────────────────────────────────
log "=== FASE 2: gemma4:e4b-it-q8_0 — F/Q/L framework ==="
set_model "gemma4:e4b-it-q8_0"
run_framework "gemma4:e4b-it-q8_0" "results/framework_gemma4_e4b-q8"
log "FASE 2 concluída."

# ── FASE 3: qwen3.5:27b direct + framework ────────────────────────────────────
log "=== FASE 3: qwen3.5:27b — T/C/Q/L/M direct + F/Q/L framework ==="
run_direct "qwen3.5:27b" T C Q L M
set_model "qwen3.5:27b"
run_framework "qwen3.5:27b" "results/framework_qwen3.5_27b"
log "FASE 3 concluída."

# ── FASE 4: qwen3.6:27b direct + framework ────────────────────────────────────
log "=== FASE 4: qwen3.6:27b — T/C/Q/L/M direct + F/Q/L framework ==="
run_direct "qwen3.6:27b" T C Q L M
set_model "qwen3.6:27b"
run_framework "qwen3.6:27b" "results/framework_qwen3.6_27b"
log "FASE 4 concluída."

# ── Restaurar config padrão ───────────────────────────────────────────────────
log "=== Restaurando modelo padrão: qwen3.5:9b ==="
set_model "qwen3.5:9b"

log "=== OVERNIGHT BATCH COMPLETO ==="
