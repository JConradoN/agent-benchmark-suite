#!/usr/bin/env python3
"""
Agent Benchmark Suite — CLI runner.

Usage:
  python run.py                                    # Ollama direct, all series, default model
  python run.py --series Q T                       # only Q and T series
  python run.py --model gemma4:26b-a4b-it-q4_K_M
  python run.py --think
  python run.py --runs 5
  python run.py --scenario Q1 T3 F2
  python run.py --report

  # Framework providers (use real Hermes/Aurelia agents):
  python run.py --provider hermes --series F Q L
  python run.py --provider hermes --model gemma4:e4b-it-q4_K_M --series F
  python run.py --provider aurelia --series F Q L
  python run.py --provider aurelia --aurelia-url http://localhost:18790
"""
import argparse
import sys

from abs.config import RunConfig, ProviderConfig
from abs.runner import BenchmarkRunner
from abs.framework_runner import FrameworkRunner
from abs.reporter import summarize
from scenarios import ALL_SCENARIOS, SERIES_MAP
from scenarios.f_series import F_SERIES

_FRAMEWORK_SERIES = {"F", "Q", "L"}


def parse_args():
    p = argparse.ArgumentParser(description="Agent Benchmark Suite")
    p.add_argument("--provider", default="ollama", choices=["ollama", "hermes", "aurelia", "llama-server"],
                   help="Provider to use (default: ollama)")
    p.add_argument("--model", default="gemma4:e4b-it-q4_K_M",
                   help="Model tag (Ollama) or Hermes -m flag")
    p.add_argument("--base-url", default="http://localhost:11434",
                   help="Ollama base URL")
    p.add_argument("--aurelia-url", default="http://localhost:18790",
                   help="Aurelia Chat API base URL")
    p.add_argument("--series", nargs="+", choices=["Q", "T", "C", "L", "M", "F"])
    p.add_argument("--scenario", nargs="+", help="Specific scenario IDs (e.g. Q1 F3)")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--timeout", type=int, default=120,
                   help="HTTP timeout in seconds per request (default: 120)")
    p.add_argument("--think", action="store_true")
    p.add_argument("--no-think", action="store_true",
                   help="Disable thinking for llama-server (prepends /no_think to user messages)")
    p.add_argument("--no-think-prefix", action="store_true",
                   help="H1: injeta /no_think no system prompt (suprime CoT verbal do Qwen3)")
    p.add_argument("--grounding-prefix", action="store_true",
                   help="H2: injeta instrução anti-alucinação no system prompt")
    p.add_argument("--max-tokens", type=int, default=2048,
                   help="Max tokens for llama-server responses (default: 2048)")
    p.add_argument("--num-ctx", type=int, default=4096,
                   help="Context window size in tokens for Ollama (default: 4096)")
    p.add_argument("--output-dir", default="results")
    p.add_argument("--report", action="store_true")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def _build_framework_runner(args) -> FrameworkRunner:
    if args.provider == "hermes":
        from abs.providers.hermes_provider import HermesProvider
        provider = HermesProvider(model=args.model, timeout=args.timeout)
    elif args.provider == "aurelia":
        from abs.providers.aurelia_provider import AureliaProvider
        provider = AureliaProvider(base_url=args.aurelia_url, timeout=args.timeout)
    else:
        raise ValueError(f"Unknown framework provider: {args.provider}")

    return FrameworkRunner(
        provider=provider,
        runs_per_scenario=args.runs,
        output_dir=args.output_dir,
        verbose=args.verbose,
    )


def _select_scenarios(args):
    all_with_f = ALL_SCENARIOS + F_SERIES
    if args.scenario:
        ids = set(args.scenario)
        scenarios = [s for s in all_with_f if s.id in ids]
        missing = ids - {s.id for s in scenarios}
        if missing:
            print(f"Unknown scenario IDs: {missing}")
            sys.exit(1)
        return scenarios
    if args.series:
        scenarios = []
        for s in args.series:
            scenarios.extend(SERIES_MAP[s])
        return scenarios
    # Default: if framework provider, run F+Q+L; if ollama, run all (no F)
    if args.provider != "ollama":
        return F_SERIES + SERIES_MAP["Q"] + SERIES_MAP["L"]
    return ALL_SCENARIOS


def main():
    args = parse_args()

    if args.report:
        summarize(args.output_dir)
        return

    scenarios = _select_scenarios(args)

    if args.provider == "llama-server":
        from abs.providers.llama_server import LlamaServerProvider
        cfg = RunConfig(
            provider=ProviderConfig(
                base_url=args.base_url,
                model=args.model,
                timeout=args.timeout,
            ),
            runs_per_scenario=args.runs,
            output_dir=args.output_dir,
            verbose=args.verbose,
        )
        runner = BenchmarkRunner(cfg, provider_instance=LlamaServerProvider(cfg.provider, no_think=args.no_think, max_tokens=args.max_tokens))
        label = args.model
    elif args.provider == "ollama":
        cfg = RunConfig(
            provider=ProviderConfig(
                base_url=args.base_url,
                model=args.model,
                timeout=args.timeout,
                think=args.think,
                num_ctx=args.num_ctx,
            ),
            runs_per_scenario=args.runs,
            output_dir=args.output_dir,
            verbose=args.verbose,
            no_think_prefix=args.no_think_prefix,
            grounding_prefix=args.grounding_prefix,
        )
        runner = BenchmarkRunner(cfg)
        label = cfg.provider.model
    else:
        runner = _build_framework_runner(args)
        label = f"{args.provider} / {args.model}"

    print(f"Provider : {args.provider}")
    print(f"Model    : {label}")
    print(f"Runs     : {args.runs}x per scenario")
    print(f"Scenarios: {len(scenarios)} ({', '.join(s.id for s in scenarios)})")
    print(f"Output   : {args.output_dir}/")
    print()

    try:
        for scenario in scenarios:
            print(f"[{scenario.id}] {scenario.name}")
            results = runner.run_scenario(scenario)
            if not args.verbose:
                for r in results:
                    scores_str = " | ".join(f"{k}={v}" for k, v in r["scores"].items())
                    lat = f"{r['latency_ms']}ms"
                    tps = f"  {r['tok_per_s']} tok/s" if r.get("tok_per_s") else ""
                    loop = " LOOP!" if r.get("loop_exhausted") else ""
                    print(f"  run {r['run_idx']+1}: {scores_str}  {lat}{tps}{loop}")
    finally:
        runner.close()

    print()
    print("=== Summary ===")
    summarize(args.output_dir)


if __name__ == "__main__":
    main()
