"""FrameworkRunner — runs scenarios through Hermes or Aurelia framework providers.

Unlike BenchmarkRunner (Ollama direct), framework runners do NOT inject mock tool
responses. The framework handles tool execution natively using its own toolset.

For comparable cross-framework results use:
  - Q/L series (no tools) — directly comparable
  - F series — tasks designed around real tools each framework has
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from abs.providers.base import Provider
from abs.scenario import Scenario
from abs.scorer import score_response


class FrameworkRunner:
    def __init__(self, provider: Provider, runs_per_scenario: int = 3, output_dir: str = "results", verbose: bool = False):
        self.provider = provider
        self.runs_per_scenario = runs_per_scenario
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_scenario(self, scenario: Scenario) -> list[dict]:
        results = []
        for run_idx in range(self.runs_per_scenario):
            result = self._single_run(scenario, run_idx)
            results.append(result)
            self._write_jsonl(result)
            if self.verbose:
                self._print_result(result)
        return results

    @property
    def verbose(self) -> bool:
        return False

    def _single_run(self, scenario: Scenario, run_idx: int) -> dict:
        result = self.provider.complete(scenario, run_idx)
        scores = score_response(scenario, {
            "content": result["final_output"],
            "tool_calls": result["tool_calls"],
        })
        return {
            "scenario_id": scenario.id,
            "series": scenario.series,
            "run_idx": run_idx,
            "provider": self.provider.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "final_output": result["final_output"],
            "tool_calls": result["tool_calls"],
            "tool_calls_count": result.get("tool_calls_count", 0),
            "loop_exhausted": result.get("loop_exhausted", False),
            "iterations": result.get("iterations", 1),
            "latency_ms": result["latency_ms"],
            "tok_per_s": result.get("tok_per_s"),
            "eval_count": result.get("eval_count", 0),
            "session_id": result.get("session_id"),
            "scores": scores,
        }

    def _write_jsonl(self, result: dict):
        path = self.output_dir / f"run_{result['scenario_id']}_{result['provider']}.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def _print_result(self, result: dict):
        scores_str = " | ".join(f"{k}={v}" for k, v in result["scores"].items())
        print(
            f"  [{result['scenario_id']}] run {result['run_idx']+1}"
            f" — {scores_str}"
            f" — {result['latency_ms']}ms"
        )

    def close(self):
        self.provider.close()
