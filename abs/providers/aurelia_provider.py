"""Aurelia framework provider — calls the running Aurelia daemon via HTTP Chat API."""
import time

import httpx

from abs.scenario import Scenario

_DEFAULT_URL = "http://localhost:18790"


class AureliaProvider:
    name = "aurelia"

    def __init__(self, base_url: str = _DEFAULT_URL, timeout: int = 180):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def complete(self, scenario: Scenario, run_idx: int = 0) -> dict:
        user_turns = [t for t in scenario.turns if t.role == "user"]
        # Stable session key: same scenario+run_idx maps to the same Aurelia session,
        # so multi-turn scenarios retain context across turns.
        session_key = f"abs-{scenario.id}-{run_idx}"

        final_output = ""
        total_latency_ms = 0

        for turn in user_turns:
            t0 = time.perf_counter()
            try:
                resp = self._client.post(
                    "/api/chat",
                    json={"text": turn.content, "session_key": session_key},
                )
                resp.raise_for_status()
            except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
                total_latency_ms += int((time.perf_counter() - t0) * 1000)
                status = getattr(getattr(exc, "response", None), "status_code", 0)
                return {
                    "final_output": f"[TIMEOUT/ERROR: {exc}]",
                    "tool_calls": [],
                    "tool_calls_count": 0,
                    "latency_ms": total_latency_ms,
                    "tok_per_s": None,
                    "eval_count": 0,
                    "session_id": session_key,
                    "loop_exhausted": status == 504,
                    "iterations": len(user_turns),
                }
            total_latency_ms += int((time.perf_counter() - t0) * 1000)

            data = resp.json()
            final_output = data.get("response", "")

        return {
            "final_output": final_output,
            "tool_calls": [],
            "tool_calls_count": 0,
            "latency_ms": total_latency_ms,
            "tok_per_s": None,
            "eval_count": 0,
            "session_id": session_key,
            "loop_exhausted": False,
            "iterations": len(user_turns),
        }

    def close(self) -> None:
        self._client.close()
