#!/usr/bin/env python3
"""
Agent Benchmark Suite — CLI runner.

Usage:
  python run.py                          # all series, default model (e4b)
  python run.py --series Q T            # only Q and T series
  python run.py --model gemma4:26b-a4b-it-q4_K_M
  python run.py --model gemma4:e4b-it-q4_K_M --think
  python run.py --runs 5                # 5 runs per scenario
  python run.py --scenario Q1 T3       # specific scenarios
  python run.py --report               # show summary of existing results
"""
import argparse
import sys
from pathlib import Path

from abs.config import RunConfig, ProviderConfig
from abs.runner import BenchmarkRunner
from abs.reporter import summarize
from scenarios import ALL_SCENARIOS, SERIES_MAP


def parse_args():
    p = argparse.ArgumentParser(description="Agent Benchmark Suite")
    p.add_argument("--model", default="gemma4:e4b-it-q4_K_M")
    p.add_argument("--base-url", default="http://localhost:11434")
    p.add_argument("--series", nargs="+", choices=["Q", "T", "C", "L", "M"])
    p.add_argument("--scenario", nargs="+", help="Run specific scenario IDs (e.g. Q1 T3)")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--think", action="store_true")
    p.add_argument("--output-dir", default="results")
    p.add_argument("--report", action="store_true", help="Show summary of existing results and exit")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    if args.report:
        summarize(args.output_dir, model=args.model if args.model != "gemma4:e4b-it-q4_K_M" else None)
        return

    cfg = RunConfig(
        provider=ProviderConfig(
            base_url=args.base_url,
            model=args.model,
            think=args.think,
        ),
        runs_per_scenario=args.runs,
        output_dir=args.output_dir,
        verbose=args.verbose,
    )

    # Select scenarios
    if args.scenario:
        ids = set(args.scenario)
        scenarios = [s for s in ALL_SCENARIOS if s.id in ids]
        missing = ids - {s.id for s in scenarios}
        if missing:
            print(f"Unknown scenario IDs: {missing}")
            sys.exit(1)
    elif args.series:
        scenarios = []
        for s in args.series:
            scenarios.extend(SERIES_MAP[s])
    else:
        scenarios = ALL_SCENARIOS

    print(f"Model  : {cfg.provider.model}")
    print(f"Think  : {cfg.provider.think}")
    print(f"Runs   : {cfg.runs_per_scenario}x per scenario")
    print(f"Scenarios: {len(scenarios)} ({', '.join(s.id for s in scenarios)})")
    print(f"Output : {cfg.output_dir}/")
    print()

    runner = BenchmarkRunner(cfg)
    try:
        for scenario in scenarios:
            print(f"[{scenario.id}] {scenario.name}")
            results = runner.run_scenario(scenario)
            if not args.verbose:
                for r in results:
                    scores_str = " | ".join(f"{k}={v}" for k, v in r["scores"].items())
                    loop = " LOOP!" if r["loop_exhausted"] else ""
                    print(
                        f"  run {r['run_idx']+1}: {scores_str}"
                        f"  {r['latency_ms']}ms  {r['tok_per_s']} tok/s"
                        f"  tools={r['tool_calls_count']}{loop}"
                    )
    finally:
        runner.close()

    print()
    print("=== Summary ===")
    summarize(args.output_dir)


if __name__ == "__main__":
    main()
