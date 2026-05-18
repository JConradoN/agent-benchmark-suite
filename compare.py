#!/usr/bin/env python3
"""
Compare results between two models or two runs.

Usage:
  python compare.py --models gemma4:e4b-it-q4_K_M gemma4:26b-a4b-it-q4_K_M
  python compare.py --series T C          # filter by series
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    _RICH = True
except ImportError:
    _RICH = False


def load_results(results_dir: str, models: list[str]) -> dict[str, dict[str, list[dict]]]:
    """Returns {model: {scenario_id: [runs]}}"""
    data: dict[str, dict[str, list[dict]]] = {m: defaultdict(list) for m in models}
    for f in Path(results_dir).glob("run_*.jsonl"):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r["model"] in data:
                    data[r["model"]][r["scenario_id"]].append(r)
    return data


def avg(vals):
    valid = [v for v in vals if isinstance(v, (int, float)) and v >= 0]
    return sum(valid) / len(valid) if valid else None


def fmt(v):
    if v is None:
        return "  —"
    return f"{v:.2f}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs=2, required=True, metavar="MODEL")
    p.add_argument("--results-dir", default="results")
    p.add_argument("--series", nargs="+", choices=["Q", "T", "C", "L", "M"])
    args = p.parse_args()

    data = load_results(args.results_dir, args.models)
    m1, m2 = args.models

    # Collect all scenario IDs
    all_ids = sorted(set(list(data[m1].keys()) + list(data[m2].keys())))
    if args.series:
        all_ids = [sid for sid in all_ids if sid[0] in args.series]

    if _RICH:
        console = Console()
        table = Table(title=f"Comparison: {m1} vs {m2}", show_lines=True)
        table.add_column("ID", style="bold cyan", width=6)
        table.add_column(f"{m1[:24]} QUAL", justify="right")
        table.add_column(f"{m2[:24]} QUAL", justify="right")
        table.add_column(f"{m1[:24]} TOOL", justify="right")
        table.add_column(f"{m2[:24]} TOOL", justify="right")
        table.add_column(f"{m1[:10]} ms", justify="right")
        table.add_column(f"{m2[:10]} ms", justify="right")

        for sid in all_ids:
            r1 = data[m1][sid]
            r2 = data[m2][sid]
            q1 = avg([r["scores"].get("QUAL", -1) for r in r1])
            q2 = avg([r["scores"].get("QUAL", -1) for r in r2])
            t1 = avg([r["scores"].get("TOOL", -1) for r in r1])
            t2 = avg([r["scores"].get("TOOL", -1) for r in r2])
            ms1 = avg([r["latency_ms"] for r in r1])
            ms2 = avg([r["latency_ms"] for r in r2])
            table.add_row(
                sid,
                fmt(q1), fmt(q2),
                fmt(t1), fmt(t2),
                f"{int(ms1)}" if ms1 else "—",
                f"{int(ms2)}" if ms2 else "—",
            )
        console.print(table)
    else:
        print(f"{'ID':<6} | {'QUAL '+m1[:10]:>14} | {'QUAL '+m2[:10]:>14} | {'ms '+m1[:6]:>10} | {'ms '+m2[:6]:>10}")
        for sid in all_ids:
            r1 = data[m1][sid]
            r2 = data[m2][sid]
            q1 = fmt(avg([r["scores"].get("QUAL", -1) for r in r1]))
            q2 = fmt(avg([r["scores"].get("QUAL", -1) for r in r2]))
            ms1 = avg([r["latency_ms"] for r in r1])
            ms2 = avg([r["latency_ms"] for r in r2])
            print(f"{sid:<6} | {q1:>14} | {q2:>14} | {int(ms1) if ms1 else '—':>10} | {int(ms2) if ms2 else '—':>10}")


if __name__ == "__main__":
    main()
