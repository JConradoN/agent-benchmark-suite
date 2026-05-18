"""Hermes framework provider — calls `hermes chat` as a subprocess."""
import re
import subprocess
import time

from abs.scenario import Scenario

_SESSION_RE = re.compile(r"^session_id:\s*(\S+)", re.MULTILINE)


class HermesProvider:
    name = "hermes"

    def __init__(
        self,
        hermes_bin: str = "hermes",
        ollama_provider: str = "custom",
        model: str | None = None,
        max_turns: int = 10,
        timeout: int = 180,
    ):
        self.hermes_bin = hermes_bin
        self.ollama_provider = ollama_provider
        self.model = model
        self.max_turns = max_turns
        self.timeout = timeout

    def complete(self, scenario: Scenario, run_idx: int = 0) -> dict:
        user_turns = [t for t in scenario.turns if t.role == "user"]
        session_id: str | None = None
        final_output = ""
        total_latency_ms = 0

        for turn in user_turns:
            cmd = [
                self.hermes_bin, "chat",
                "-Q",
                "--provider", self.ollama_provider,
                "--max-turns", str(self.max_turns),
                "--source", "benchmark",
                "--ignore-rules",
            ]
            if self.model:
                cmd += ["-m", self.model]
            if session_id:
                cmd += ["--resume", session_id]
            cmd += ["-q", turn.content]

            t0 = time.perf_counter()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            total_latency_ms += int((time.perf_counter() - t0) * 1000)

            stdout = result.stdout

            # Extract session_id from output
            m = _SESSION_RE.search(stdout)
            if m:
                session_id = m.group(1)

            # Response text: everything except the session_id line
            lines = [l for l in stdout.splitlines() if not l.startswith("session_id:")]
            final_output = "\n".join(lines).strip()

        return {
            "final_output": final_output,
            "tool_calls": [],
            "tool_calls_count": 0,
            "latency_ms": total_latency_ms,
            "tok_per_s": None,
            "eval_count": 0,
            "session_id": session_id,
            "loop_exhausted": False,
            "iterations": len(user_turns),
        }

    def close(self) -> None:
        pass
