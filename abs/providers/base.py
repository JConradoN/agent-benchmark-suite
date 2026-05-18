"""Base protocol for benchmark providers."""
from typing import Protocol, runtime_checkable

from abs.scenario import Scenario


@runtime_checkable
class Provider(Protocol):
    name: str

    def complete(self, scenario: Scenario, run_idx: int = 0) -> dict:
        """Run all turns of a scenario and return a result dict.

        Returns:
            final_output: str — the model's last response
            tool_calls: list — tool calls made (framework may be empty)
            latency_ms: int — total wall-clock latency in ms
            tok_per_s: float | None — throughput if available
            eval_count: int — total tokens generated
            session_id: str | None — session identifier (for resume)
        """
        ...

    def close(self) -> None: ...
