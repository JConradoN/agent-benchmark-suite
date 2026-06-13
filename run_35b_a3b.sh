#!/bin/bash
# ABS completo — qwen3.6:35b-a3b
# Direct: T C Q L M (2 runs cada)
# Framework: F Q L via Aurelia + Hermes (2 runs cada, timeout 600s)

set -uo pipefail
cd /home/conrado/repos/estudo/agent-benchmark-suite

MODEL="qwen3.6:35b-a3b"
OUTDIR="results/framework_qwen3.6_35b-a3b"
LOG="/tmp/abs_35b_a3b.log"
AURELIA_CONFIG="/home/conrado/.aurelia/config/app.json"
HERMES_CONFIG="/home/conrado/.hermes/config.yaml"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== ABS completo: $MODEL ==="

# ── Pré-condições ────────────────────────────────────────────────────────────
# Parar Aurelia e descarregar o modelo antes dos direct runs.
# Necessário porque Aurelia segura o runner com ctx=32768 (keep_alive=Forever).
# O ABS pede num_ctx=4096 → Ollama trava tentando recarregar → 500.
log "Parando aurelia.service..."
systemctl --user stop aurelia.service
sleep 3

log "Descarregando modelo (keep_alive=0)..."
python3 -c "
import httpx
try:
    httpx.post('http://localhost:11434/api/generate',
        json={'model':'$MODEL','keep_alive':0,'prompt':'','stream':False},
        timeout=15)
except: pass
"

# Aguarda VRAM esvaziar de fato (sem timeout fixo)
log "Aguardando VRAM < 1 GB..."
python3 -c "
import subprocess, time, sys
for _ in range(60):
    ps = subprocess.run(['docker','exec','ollama','ollama','ps'], capture_output=True, text=True).stdout
    if '$MODEL' not in ps:
        vram = subprocess.run(
            ['docker','exec','ollama','nvidia-smi','--query-gpu=memory.used','--format=csv,noheader'],
            capture_output=True, text=True).stdout
        used = sum(int(l.replace('MiB','').strip()) for l in vram.strip().splitlines() if l.strip())
        if used < 1000:
            print(f'VRAM livre: {used} MiB')
            sys.exit(0)
    time.sleep(5)
print('timeout aguardando unload')
sys.exit(1)
"
RC=$?
if [ $RC -ne 0 ]; then
    log "ERRO: modelo não descarregou em 5min — abortando"
    exit 1
fi
log "Modelo descarregado. FASE 1 vai carregar com num_ctx=4096 no primeiro request."

# ── DIRECT: T C Q L M ────────────────────────────────────────────────────────
log "=== FASE 1: direct ollama — séries T C Q L M ==="
python3 run.py --provider ollama --model "$MODEL" --series T C Q L M --runs 2 2>&1 | tee -a "$LOG"
log "FASE 1 concluída."

# ── Preparar framework ────────────────────────────────────────────────────────
mkdir -p "$OUTDIR"

# Atualizar Hermes para 35b-a3b
sed -i "s/^  default: .*/  default: $MODEL/" "$HERMES_CONFIG"
log "Hermes config atualizado: $(grep 'default:' "$HERMES_CONFIG" | head -1)"

# Reiniciar Aurelia com 35b-a3b (config já aponta para 35b-a3b)
log "Reiniciando aurelia.service com $MODEL..."
systemctl --user restart aurelia.service
sleep 10
STATUS=$(systemctl --user is-active aurelia.service)
log "aurelia.service: $STATUS"

# ── FRAMEWORK: Aurelia (F Q L) ────────────────────────────────────────────────
log "=== FASE 2: framework aurelia — séries F Q L ==="
python3 run.py --provider aurelia --series F Q L --runs 2 --timeout 600 --output-dir "$OUTDIR" 2>&1 | tee -a "$LOG"
log "FASE 2 concluída."

# ── FRAMEWORK: Hermes (F Q L) ─────────────────────────────────────────────────
log "=== FASE 3: framework hermes — séries F Q L ==="
python3 run.py --provider hermes --model "$MODEL" --series F Q L --runs 2 --timeout 600 --output-dir "$OUTDIR" 2>&1 | tee -a "$LOG"
log "FASE 3 concluída."

log "=== ABS $MODEL COMPLETO ==="
log "Resultados direct: results/run_*${MODEL//:/_}* (ou similar)"
log "Resultados framework: $OUTDIR/"
