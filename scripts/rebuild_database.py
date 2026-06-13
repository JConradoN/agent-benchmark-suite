#!/usr/bin/env python3
"""
Rebuild abs_database_validated.json from all JSONL files in results/.

Reads every JSONL file, normalizes model names, applies the exclusion list,
and writes a fresh validated database.

Usage:
  python3 scripts/rebuild_database.py [--dry-run]
"""
import json
import os
import re
import sys
import glob
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"
OUTPUT_FILE = RESULTS_DIR / "abs_database_validated.json"

# Normalize raw model names to canonical display names
MODEL_ALIASES = {
    "gemma4:26b-a4b-it-q4_K_M": "gemma4:26b",
    "gemma4:e4b-it-q4_K_M":     "gemma4:e4b-q4",
    "gemma4:e4b-it-q8_0":        "gemma4:e4b-q8",
    "granite4.1:8b":             "granite4.1:8b",
    "granite4.1:30b":            "granite4.1:30b",
    "qwen3.5:9b":                "qwen3.5:9b",
    "qwen3.5:9b-48k":            "qwen3.5:9b-48k",
    "qwen3.5:27b":               "qwen3.5:27b",
    "qwen3.6:27b":               "qwen3.6:27b",
    "qwen3.6:35b-a3b":           "qwen3.6:35b-a3b",
    "lfm2:24b":                  "lfm2:24b",
    "mixtral:8x7b":              "mixtral:8x7b",
}

# Model inferred from directory name for framework runs
FRAMEWORK_DIR_MODEL = {
    "framework_gemma4_26b-a4b-it-q4_K_M": "gemma4:26b",
    "framework_gemma4_e4b-q4":             "gemma4:e4b-q4",
    "framework_gemma4_e4b-q8":             "gemma4:e4b-q8",
    "framework_granite4.1_8b":             "granite4.1:8b",
    "framework_granite4.1_30b":            "granite4.1:30b",
    "framework_qwen3.5_9b":               "qwen3.5:9b",
    "framework_qwen3.5_27b":              "qwen3.5:27b",
    "framework_qwen3.6_27b":              "qwen3.6:27b",
    "framework_qwen3.6_35b-a3b":          "qwen3.6:35b-a3b",
}

# Exclusion rules — applied after normalization
# scope: "all" | "direct" | "framework" | "aurelia" | "hermes" | "aurelia_F"
EXCLUSIONS = [
    {"model": "lfm2:24b",        "scope": "direct",    "reason": "descartado na Fase 1 — sem tool use"},
    {"model": "qwen3.5:9b-48k",  "scope": "direct",    "reason": "modelfile auxiliar, não pertence ao setup padrão"},
    {"model": "granite4.1:30b",  "scope": "framework", "reason": "performance degradada (CPU offload excessivo)"},
    {"model": "qwen3.6:27b",     "scope": "framework", "reason": "descartado — inviável continuar"},
    {"model": "qwen3.5:27b",     "scope": "aurelia",   "reason": "CORROMPIDO — timeouts em massa, Q-series 0.00"},
    # qwen3.5:9b aurelia F: runs corrompidos eliminados via dedup (últimos 3 = runs válidos de 15:18)
]

# Validity thresholds for framework runs
INVALID_LAT_MAX = 200   # ms — lat < this + QUAL=0 → INVALID_NO_CALL
TIMEOUT_LAT_MIN = 119000  # ms — lat > this → HARD_TIMEOUT


def normalize_model(raw_model: str | None) -> str | None:
    if raw_model is None:
        return None
    return MODEL_ALIASES.get(raw_model, raw_model)


def classify_framework_validity(record: dict) -> str:
    """Classify a framework run record as VALID or reason for invalidity."""
    lat = record.get("latency_ms", 0)
    qual = record.get("primary_score", 0)
    if lat < INVALID_LAT_MAX and qual == 0:
        return "INVALID_NO_CALL"
    if lat > TIMEOUT_LAT_MIN and qual == 0:
        return "HARD_TIMEOUT"
    if lat < INVALID_LAT_MAX and qual > 0:
        return "INSTANT_NONZERO"
    return "VALID"


def should_exclude(model: str, source: str, provider: str | None, series: str | None) -> tuple[bool, str | None]:
    for ex in EXCLUSIONS:
        if ex["model"] != model:
            continue
        scope = ex["scope"]
        if scope == "all":
            return True, ex["reason"]
        if scope == "direct" and source == "direct":
            return True, ex["reason"]
        if scope == "framework" and source == "framework":
            return True, ex["reason"]
        if scope == "aurelia" and provider == "aurelia":
            return True, ex["reason"]
        if scope == "hermes" and provider == "hermes":
            return True, ex["reason"]
        if scope == "aurelia_F" and provider == "aurelia" and series == "F":
            return True, ex["reason"]
    return False, None


RUNS_PER_SCENARIO = 3  # standard run count


def _deduplicate_runs(raw_records: list[dict]) -> list[dict]:
    """Keep only the last RUNS_PER_SCENARIO runs per (model, scenario_id, provider) key.

    Multiple batches append to the same JSONL file. The most recent batch is
    authoritative — select the last N records (where N=RUNS_PER_SCENARIO).
    """
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for r in raw_records:
        key = (r["model"], r["scenario_id"], r.get("provider"))
        groups[key].append(r)
    result = []
    for records in groups.values():
        result.extend(records[-RUNS_PER_SCENARIO:])
    return result


def load_direct_runs() -> list[dict]:
    """Load all direct (Ollama) JSONL files from results root."""
    raw = []
    for fpath in glob.glob(str(RESULTS_DIR / "run_*.jsonl")):
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                # Direct runs have model field; framework orphans at root have provider
                if d.get("provider") and not d.get("model"):
                    continue  # skip orphan framework runs at root
                raw_model = d.get("model")
                model = normalize_model(raw_model)
                if model is None:
                    continue  # no model identity — skip
                scores = d.get("scores", {})
                primary_score = scores.get("TOOL") or scores.get("QUAL", 0)
                lat_score = scores.get("LAT", 0)
                raw.append({
                    "model": model,
                    "source": "direct",
                    "provider": None,
                    "scenario_id": d["scenario_id"],
                    "series": d["series"],
                    "primary_score": primary_score,
                    "lat_score": lat_score,
                    "tok_per_s": d.get("tok_per_s"),
                    "latency_ms": d.get("latency_ms", 0),
                    "excluded": False,
                    "exclude_note": None,
                })
    records = _deduplicate_runs(raw)
    if len(raw) != len(records):
        print(f"  Deduplicated direct: {len(raw)} → {len(records)} records", file=sys.stderr)
    return records


def load_framework_runs() -> list[dict]:
    """Load all framework JSONL files from framework_* subdirs."""
    raw = []
    for dirpath in glob.glob(str(RESULTS_DIR / "framework_*")):
        dirname = os.path.basename(dirpath)
        model = FRAMEWORK_DIR_MODEL.get(dirname)
        if model is None:
            print(f"  WARNING: unknown framework dir '{dirname}' — skipping", file=sys.stderr)
            continue
        for fpath in glob.glob(os.path.join(dirpath, "run_*.jsonl")):
            with open(fpath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    provider = d.get("provider", "unknown")
                    scores = d.get("scores", {})
                    primary_score = scores.get("QUAL", 0)
                    lat_score = scores.get("LAT", 0)
                    raw.append({
                        "model": model,
                        "source": "framework",
                        "provider": provider,
                        "scenario_id": d["scenario_id"],
                        "series": d["series"],
                        "primary_score": primary_score,
                        "lat_score": lat_score,
                        "tok_per_s": d.get("tok_per_s"),
                        "latency_ms": d.get("latency_ms", 0),
                        "excluded": False,
                        "exclude_note": None,
                    })
    records = _deduplicate_runs(raw)
    if len(raw) != len(records):
        print(f"  Deduplicated framework: {len(raw)} → {len(records)} records", file=sys.stderr)
    return records


def apply_exclusions(records: list[dict]) -> list[dict]:
    for r in records:
        excluded, note = should_exclude(r["model"], r["source"], r["provider"], r["series"])
        if excluded:
            r["excluded"] = True
            r["exclude_note"] = note
            continue
        # Framework validity check
        if r["source"] == "framework":
            validity = classify_framework_validity(r)
            if validity != "VALID":
                r["excluded"] = True
                r["exclude_note"] = f"validity={validity}"
    return records


def compute_summary(records: list[dict]) -> dict:
    """Compute aggregated scores per model per source/provider."""
    valid = [r for r in records if not r["excluded"]]

    # Direct scores
    direct = defaultdict(lambda: defaultdict(list))
    toks = defaultdict(list)
    for r in valid:
        if r["source"] == "direct":
            direct[r["model"]][r["series"]].append(r["primary_score"])
            if r["tok_per_s"]:
                toks[r["model"]].append(r["tok_per_s"])

    direct_summary = {}
    for model, series_map in direct.items():
        series_avgs = {s: round(sum(v)/len(v), 2) for s, v in series_map.items()}
        all_scores = [v for vs in series_map.values() for v in vs]
        overall = round(sum(all_scores)/len(all_scores), 2) if all_scores else 0
        tok_avg = round(sum(toks[model])/len(toks[model]), 1) if toks[model] else None
        direct_summary[model] = {**series_avgs, "overall": overall, "tok_per_s": tok_avg}

    # Framework scores (per model per provider)
    fw = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in valid:
        if r["source"] == "framework":
            fw[r["model"]][r["provider"]][r["series"]].append(r["primary_score"])

    fw_summary = {}
    for model, prov_map in fw.items():
        fw_summary[model] = {}
        for provider, series_map in prov_map.items():
            series_avgs = {s: round(sum(v)/len(v), 2) for s, v in series_map.items()}
            all_scores = [v for vs in series_map.values() for v in vs]
            overall = round(sum(all_scores)/len(all_scores), 2) if all_scores else 0
            fw_summary[model][provider] = {**series_avgs, "overall": overall}

    return {"direct": direct_summary, "framework": fw_summary}


def main():
    dry_run = "--dry-run" in sys.argv
    os.chdir(RESULTS_DIR.parent)

    print("Loading direct runs...")
    direct = load_direct_runs()
    print(f"  {len(direct)} records")

    print("Loading framework runs...")
    framework = load_framework_runs()
    print(f"  {len(framework)} records")

    all_records = direct + framework
    print(f"Total: {len(all_records)} records before exclusions")

    apply_exclusions(all_records)
    excluded_count = sum(1 for r in all_records if r["excluded"])
    print(f"Excluded: {excluded_count} records")
    print(f"Valid: {len(all_records) - excluded_count} records")

    summary = compute_summary(all_records)

    print("\n=== DIRECT SCORES ===")
    models_ranked = sorted(summary["direct"].items(), key=lambda x: -x[1].get("overall", 0))
    print(f"{'Model':<20} {'T':>5} {'C':>5} {'Q':>5} {'L':>5} {'M':>5} {'Overall':>8} {'tok/s':>6}")
    for model, s in models_ranked:
        print(f"{model:<20} {s.get('T','--'):>5} {s.get('C','--'):>5} {s.get('Q','--'):>5} {s.get('L','--'):>5} {s.get('M','--'):>5} {s.get('overall','--'):>8} {s.get('tok_per_s','--'):>6}")

    print("\n=== FRAMEWORK SCORES ===")
    for model in sorted(summary["framework"]):
        for provider in sorted(summary["framework"][model]):
            s = summary["framework"][model][provider]
            print(f"{model:<20} [{provider:7}] F={s.get('F','--')} Q={s.get('Q','--')} L={s.get('L','--')} → {s.get('overall','--')}")

    if dry_run:
        print("\n[dry-run] Not writing output file.")
        return

    output = {
        "version": "validated_v2",
        "notes": "Rebuilt from all JSONL files 2026-05-19 — includes gemma4:e4b-q4 framework and qwen3.5:9b Aurelia F-series",
        "exclusions": EXCLUSIONS,
        "summary": summary,
        "records": all_records,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE) // 1024}KB)")


if __name__ == "__main__":
    main()
