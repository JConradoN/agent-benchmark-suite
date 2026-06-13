#!/bin/bash
# ABS Overnight Batch — continua de onde parou até relatório final
# Sequência: aguarda FASE 4 Hermes → FASE 5 (e4b-q8_0) → FASE 6 (granite3.1) → relatório
# Log: /tmp/abs_overnight.log

set -euo pipefail
cd /home/conrado/repos/estudo/agent-benchmark-suite
LOG=/tmp/abs_overnight.log
exec > >(tee -a "$LOG") 2>&1

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
log "=========================================="
log "ABS OVERNIGHT INICIADO"
log "=========================================="

# ── Retry runner ──────────────────────────────────────────────────────────────
run_with_retry() {
    local desc="$1"; shift
    local attempt=1
    while [ $attempt -le 3 ]; do
        log ">>> $desc (tentativa $attempt/3)"
        if python3 run.py "$@"; then
            log "<<< $desc — OK"
            return 0
        fi
        log "!!! $desc FALHOU (tentativa $attempt/3)"
        attempt=$((attempt + 1))
        [ $attempt -le 3 ] && sleep 30
    done
    log "!!! $desc — 3 tentativas esgotadas, pulando"
    return 1
}

# ── Verificar runs completos ──────────────────────────────────────────────────
runs_in_file() {
    local f="$1"
    [ -f "$f" ] && wc -l < "$f" || echo 0
}

# ─────────────────────────────────────────────────────────────────────────────
# AGUARDAR FASE 4 HERMES (processo atual)
# ─────────────────────────────────────────────────────────────────────────────
log "Aguardando FASE 4 Hermes terminar..."
while pgrep -f "run.py --provider hermes" > /dev/null; do
    sleep 15
done
log "FASE 4 Hermes — processo encerrado"

# Verificar e completar runs faltando em FASE 4 Hermes
for scenario in L1 L2 L3; do
    f="results/framework_granite4.1_8b/run_${scenario}_hermes.jsonl"
    runs=$(runs_in_file "$f")
    if [ "$runs" -lt 2 ]; then
        needed=$((2 - runs))
        log "  ${scenario}_hermes: $runs/2 runs — rodando $needed restante(s)"
        run_with_retry "FASE 4 Hermes $scenario (faltando)" \
            --provider hermes --model granite4.1:8b \
            --scenario "$scenario" --runs "$needed" --timeout 600 \
            --output-dir results/framework_granite4.1_8b || true
    else
        log "  ${scenario}_hermes: $runs runs — OK"
    fi
done

# ─────────────────────────────────────────────────────────────────────────────
# RESTAURAR CONFIGS DE MODELO
# ─────────────────────────────────────────────────────────────────────────────
log "Restaurando modelos padrão (e4b)..."
python3 -c "
import json
cfg = '/home/conrado/.aurelia/config/app.json'
with open(cfg) as f: d = json.load(f)
d['default_model'] = 'gemma4:e4b-it-q4_K_M'
with open(cfg, 'w') as f: json.dump(d, f, indent=2)
print('aurelia → e4b')
"
# Hermes
python3 -c "
import re, pathlib
cfg = pathlib.Path.home() / '.hermes/config.yaml'
txt = cfg.read_text()
txt = re.sub(r'(^  default:) .*', r'\1 gemma4:e4b-it-q4_K_M', txt, flags=re.MULTILINE)
cfg.write_text(txt)
print('hermes → e4b')
"
log "hermes → e4b"
systemctl --user restart aurelia.service
sleep 5
log "Aurelia reiniciada"

# ─────────────────────────────────────────────────────────────────────────────
# FASE 5 — gemma4:e4b-it-q8_0 direct (T C Q L M)
# ─────────────────────────────────────────────────────────────────────────────
log "=========================================="
log "FASE 5 — gemma4:e4b-it-q8_0 direct T C Q L M"
log "=========================================="

run_with_retry "FASE 5 e4b-q8_0 direct" \
    --provider ollama --model gemma4:e4b-it-q8_0 \
    --series T C Q L M --runs 2 || true

# ─────────────────────────────────────────────────────────────────────────────
# FASE 6 — granite3.1-dense:8b direct (C Q L M)
# ─────────────────────────────────────────────────────────────────────────────
log "=========================================="
log "FASE 6 — granite3.1-dense:8b direct C Q L M"
log "=========================================="

# C1 e C2 já têm 2 runs — pular
# C3 tem 1 run — adicionar 1
c3_runs=$(runs_in_file "results/run_C3_granite3.1-dense_8b.jsonl")
if [ "$c3_runs" -lt 2 ]; then
    log "C3 granite3.1: $c3_runs/2 — completando"
    run_with_retry "FASE 6 granite3.1 C3 (1 run restante)" \
        --provider ollama --model granite3.1-dense:8b \
        --scenario C3 --runs 1 || true
fi

# C4, C5, Q, L, M — ausentes completamente
run_with_retry "FASE 6 granite3.1 C4 C5" \
    --provider ollama --model granite3.1-dense:8b \
    --scenario C4 C5 --runs 2 || true

run_with_retry "FASE 6 granite3.1 Q L M" \
    --provider ollama --model granite3.1-dense:8b \
    --series Q L M --runs 2 || true

# ─────────────────────────────────────────────────────────────────────────────
# RELATÓRIO FINAL
# ─────────────────────────────────────────────────────────────────────────────
log "=========================================="
log "GERANDO RELATÓRIO FINAL"
log "=========================================="
python3 run.py --report || true

# Copiar para vault
VAULT_DEST="/mnt/vault/TEMP/ABS_REPORT_$(date '+%Y%m%d_%H%M%S').md"
latest=$(ls -t results/BENCHMARK_RESULTS_*.md 2>/dev/null | head -1)
if [ -n "$latest" ]; then
    cp "$latest" "$VAULT_DEST" && log "Relatório copiado → $VAULT_DEST"
else
    log "Nenhum relatório .md encontrado para copiar"
fi

log "=========================================="
log "OVERNIGHT CONCLUÍDO"
log "=========================================="
