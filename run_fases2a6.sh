#!/bin/bash
# Fases 2-6 do batch overnight — continua após FASE 1B concluída
set -uo pipefail

cd /home/conrado/repos/estudo/agent-benchmark-suite

TIMEOUT=600
AURELIA_BIN="/home/conrado/.aurelia/bin/aurelia"
DEFAULT_MODEL="gemma4:26b-a4b-it-q4_K_M"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

swap_model() {
    local model="$1"
    log "Config → $model"
    python3 - "$model" <<'EOF'
import json, sys
model = sys.argv[1]
with open("/home/conrado/.aurelia/config/app.json") as f:
    d = json.load(f)
d["default_model"] = model
with open("/home/conrado/.aurelia/config/app.json", "w") as f:
    json.dump(d, f, indent=2)
print(f"  aurelia config: {model}")
EOF
    python3 - "$model" <<'EOF'
import sys, re
model = sys.argv[1]
path = "/home/conrado/.hermes/config.yaml"
with open(path) as f:
    content = f.read()
content = re.sub(r"(^model:\n  default:) .*", rf"\1 {model}", content, flags=re.MULTILINE)
with open(path, "w") as f:
    f.write(content)
print(f"  hermes config: {model}")
EOF
}

restart_aurelia() {
    log "Reiniciando Aurelia..."
    pkill -f "$AURELIA_BIN" 2>/dev/null || true
    sleep 3
    "$AURELIA_BIN" >> /tmp/aurelia_batch.log 2>&1 &
    sleep 8
    local pid
    pid=$(pgrep -f "$AURELIA_BIN" | head -1)
    log "Aurelia PID: $pid"
}

run_direct() {
    local model="$1"; shift
    local series="$*"
    log "=== DIRECT: $model — séries: $series ==="
    python3 run.py --provider ollama --model "$model" \
        --series $series --runs 2 --timeout "$TIMEOUT"
}

run_framework() {
    local model="$1"
    local tag
    tag=$(echo "$model" | sed 's|[:/]|_|g')
    local outdir="results/framework_${tag}"
    mkdir -p "$outdir"
    log "=== FRAMEWORK: $model → $outdir ==="

    swap_model "$model"
    restart_aurelia

    log "  Aurelia F/Q/L..."
    python3 run.py --provider aurelia --series F Q L \
        --runs 2 --timeout "$TIMEOUT" --output-dir "$outdir" || true

    log "  Hermes F/Q/L (--model $model)..."
    python3 run.py --provider hermes --model "$model" --series F Q L \
        --runs 2 --timeout "$TIMEOUT" --output-dir "$outdir" || true
}

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2 — granite4.1:30b via frameworks (Aurelia + Hermes)
# ═══════════════════════════════════════════════════════════════════════════════
log "FASE 2 — granite4.1:30b frameworks..."
run_framework "granite4.1:30b"

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3 — gemma4:26b via frameworks
# ═══════════════════════════════════════════════════════════════════════════════
log "FASE 3 — gemma4:26b frameworks..."
run_framework "gemma4:26b-a4b-it-q4_K_M"

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 4 — granite4.1:8b via frameworks
# ═══════════════════════════════════════════════════════════════════════════════
log "FASE 4 — granite4.1:8b frameworks..."
run_framework "granite4.1:8b"

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 5 — gemma4:e4b-it-q8_0 direct
# ═══════════════════════════════════════════════════════════════════════════════
log "FASE 5 — gemma4:e4b-it-q8_0 direct..."
run_direct "gemma4:e4b-it-q8_0" T C Q L M

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 6 — granite3.1-dense:8b direct (C/Q/L/M)
# ═══════════════════════════════════════════════════════════════════════════════
log "FASE 6 — granite3.1-dense:8b direct (C/Q/L/M)..."
run_direct "granite3.1-dense:8b" C Q L M

# ═══════════════════════════════════════════════════════════════════════════════
# RESTAURAR CONFIG PADRÃO
# ═══════════════════════════════════════════════════════════════════════════════
log "Restaurando config padrão → $DEFAULT_MODEL"
swap_model "$DEFAULT_MODEL"
restart_aurelia

log "=== BATCH FASES 2-6 CONCLUÍDO ==="
