import json
import time
from datetime import datetime, timezone
from pathlib import Path

from abs.config import RunConfig
from abs.providers.ollama import OllamaProvider
from abs.scenario import Scenario, Turn
from abs.scorer import score_response


class BenchmarkRunner:
    def __init__(self, cfg: RunConfig):
        self.cfg = cfg
        self.provider = OllamaProvider(cfg.provider)
        self.output_dir = Path(cfg.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_scenario(self, scenario: Scenario) -> list[dict]:
        results = []
        for run_idx in range(self.cfg.runs_per_scenario):
            result = self._single_run(scenario, run_idx)
            results.append(result)
            self._write_jsonl(result)
            if self.cfg.verbose:
                self._print_result(result)
        return results

    def _single_run(self, scenario: Scenario, run_idx: int) -> dict:
        messages = [{"role": t.role, "content": t.content} for t in scenario.turns]
        tools_api = [t.to_api() for t in scenario.tools] if scenario.tools else None

        tool_calls_log: list[dict] = []
        loop_exhausted = False
        total_latency_ms = 0
        total_tok = 0
        iterations = 0
        max_iterations = 8

        while iterations < max_iterations:
            iterations += 1
            resp = self.provider.chat(messages, tools=tools_api)
            total_latency_ms += resp["latency_ms"]
            total_tok += resp["eval_count"]

            if resp["tool_calls"]:
                tool_calls_log.extend(resp["tool_calls"])
                # Append assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": resp["content"] or "",
                    "tool_calls": resp["tool_calls"],
                })
                # Inject mock responses for each tool call
                for tc in resp["tool_calls"]:
                    fn_name = tc.get("function", {}).get("name", "")
                    mock_resp = scenario.mock_tool_responses.get(fn_name, f'{{"result": "ok"}}')
                    messages.append({
                        "role": "tool",
                        "content": mock_resp,
                        "name": fn_name,
                    })
            else:
                # No more tool calls — final response
                break
        else:
            loop_exhausted = True

        scores = score_response(scenario, {**resp, "tool_calls": tool_calls_log})

        return {
            "scenario_id": scenario.id,
            "series": scenario.series,
            "run_idx": run_idx,
            "model": self.cfg.provider.model,
            "provider_url": self.cfg.provider.base_url,
            "think": self.cfg.provider.think,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "final_output": resp["content"],
            "tool_calls": tool_calls_log,
            "tool_calls_count": len(tool_calls_log),
            "loop_exhausted": loop_exhausted,
            "iterations": iterations,
            "latency_ms": total_latency_ms,
            "tok_per_s": resp["tok_per_s"],
            "eval_count": total_tok,
            "scores": scores,
        }

    def _write_jsonl(self, result: dict):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"run_{result['scenario_id']}_{result['model'].replace(':', '_')}.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def _print_result(self, result: dict):
        scores_str = " | ".join(f"{k}={v}" for k, v in result["scores"].items())
        print(
            f"  [{result['scenario_id']}] run {result['run_idx']+1}"
            f" — {scores_str}"
            f" — {result['latency_ms']}ms"
            f" — {result['tok_per_s']} tok/s"
            f" — tools={result['tool_calls_count']}"
            f" — loop={'YES' if result['loop_exhausted'] else 'no'}"
        )

    def close(self):
        self.provider.close()
