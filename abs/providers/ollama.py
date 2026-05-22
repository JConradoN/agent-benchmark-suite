import time
import httpx
from abs.config import ProviderConfig


class OllamaProvider:
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self._client = httpx.Client(base_url=cfg.base_url, timeout=cfg.timeout)

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload: dict = {
            "model": self.cfg.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.cfg.temperature, "num_ctx": 4096},
        }
        if tools:
            payload["tools"] = tools
        if self.cfg.think is not None:
            payload["think"] = self.cfg.think

        t0 = time.perf_counter()
        resp = self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        data = resp.json()
        return {
            "content": data.get("message", {}).get("content", ""),
            "tool_calls": data.get("message", {}).get("tool_calls", []),
            "latency_ms": elapsed_ms,
            "eval_count": data.get("eval_count", 0),
            "eval_duration_ns": data.get("eval_duration", 0),
            "tok_per_s": round(
                data.get("eval_count", 0) / max(data.get("eval_duration", 1) / 1e9, 0.001), 1
            ),
            "raw": data,
        }

    def close(self):
        self._client.close()
