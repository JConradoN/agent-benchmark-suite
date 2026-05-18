import json
from pathlib import Path
from collections import defaultdict

try:
    from rich.console import Console
    from rich.table import Table
    _RICH = True
except ImportError:
    _RICH = False


def summarize(results_dir: str | Path, model: str | None = None):
    results_dir = Path(results_dir)
    records: list[dict] = []

    for f in sorted(results_dir.glob("run_*.jsonl")):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if model and rec.get("model") != model:
                    continue
                records.append(rec)

    if not records:
        print("No results found.")
        return

    # Group by scenario_id
    by_scenario: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_scenario[r["scenario_id"]].append(r)

    if _RICH:
        _rich_table(by_scenario)
    else:
        _plain_table(by_scenario)


def _rich_table(by_scenario: dict[str, list[dict]]):
    console = Console()
    table = Table(title="Agent Benchmark Suite — Results", show_lines=True)

    table.add_column("ID", style="bold cyan", width=6)
    table.add_column("Series", width=6)
    table.add_column("Model", width=28)
    table.add_column("Runs", justify="right", width=5)
    table.add_column("QUAL", justify="right", width=6)
    table.add_column("TOOL", justify="right", width=6)
    table.add_column("LAT", justify="right", width=6)
    table.add_column("tok/s", justify="right", width=7)
    table.add_column("ms", justify="right", width=8)
    table.add_column("loops", justify="right", width=6)

    for sid in sorted(by_scenario):
        runs = by_scenario[sid]
        model = runs[0].get("model") or runs[0].get("provider", "?")
        series = runs[0]["series"]
        n = len(runs)

        qual = _avg([r["scores"].get("QUAL", -1) for r in runs])
        tool = _avg([r["scores"].get("TOOL", -1) for r in runs])
        lat_score = _avg([r["scores"].get("LAT", -1) for r in runs])
        tps = _avg([r["tok_per_s"] for r in runs if r.get("tok_per_s") is not None])
        ms = _avg([r["latency_ms"] for r in runs])
        loops = sum(1 for r in runs if r.get("loop_exhausted"))

        table.add_row(
            sid, series, model, str(n),
            _fmt(qual), _fmt(tool), _fmt(lat_score),
            f"{tps:.1f}", f"{int(ms)}", str(loops),
        )

    console.print(table)


def _plain_table(by_scenario: dict[str, list[dict]]):
    header = f"{'ID':<6} {'S':<2} {'Runs':>4} {'QUAL':>5} {'TOOL':>5} {'LAT':>5} {'tok/s':>7} {'ms':>8} {'loops':>6}"
    print(header)
    print("-" * len(header))
    for sid in sorted(by_scenario):
        runs = by_scenario[sid]
        n = len(runs)
        qual = _avg([r["scores"].get("QUAL", -1) for r in runs])
        tool = _avg([r["scores"].get("TOOL", -1) for r in runs])
        lat = _avg([r["scores"].get("LAT", -1) for r in runs])
        tps = _avg([r["tok_per_s"] for r in runs if r.get("tok_per_s") is not None])
        ms = _avg([r["latency_ms"] for r in runs])
        loops = sum(1 for r in runs if r.get("loop_exhausted"))
        print(
            f"{sid:<6} {runs[0]['series']:<2} {n:>4} "
            f"{_fmt(qual):>5} {_fmt(tool):>5} {_fmt(lat):>5} "
            f"{tps:>7.1f} {int(ms):>8} {loops:>6}"
        )


def _avg(vals: list) -> float:
    valid = [v for v in vals if v >= 0]
    return sum(valid) / len(valid) if valid else -1.0


def _fmt(v: float) -> str:
    return f"{v:.2f}" if v >= 0 else "  —"
