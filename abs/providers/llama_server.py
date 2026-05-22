"""Provider for llama-server (ggml-org/llama.cpp) OpenAI-compat API."""
import time
import httpx
from abs.config import ProviderConfig

_RETRY_STATUSES = {500, 502, 503}


class LlamaServerProvider:
    name = "llama-server"

    def __init__(self, cfg: ProviderConfig, no_think: bool = False, max_tokens: int = 2048):
        self.cfg = cfg
        self.no_think = no_think
        self.max_tokens = max_tokens
        self._client = httpx.Client(base_url=cfg.base_url, timeout=cfg.timeout)

    def _inject_no_think(self, messages: list[dict]) -> list[dict]:
        """Prepends /no_think to the first user message to disable Qwen3 thinking."""
        result = []
        injected = False
        for msg in messages:
            if not injected and msg.get("role") == "user":
                result.append({**msg, "content": f"/no_think\n{msg['content']}"})
                injected = True
            else:
                result.append(msg)
        return result

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if self.no_think:
            messages = self._inject_no_think(messages)
        payload: dict = {
            "model": self.cfg.model,
            "messages": messages,
            "stream": False,
            "temperature": self.cfg.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            payload["tools"] = tools

        t0 = time.perf_counter()
        for attempt in range(3):
            resp = self._client.post("/v1/chat/completions", json=payload)
            if resp.status_code not in _RETRY_STATUSES:
                break
            time.sleep(5 * (attempt + 1))
        resp.raise_for_status()
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        eval_count = usage.get("completion_tokens", 0)

        # Normalize OpenAI tool_calls format, preserving id for tool_call_id injection
        raw_tcs = message.get("tool_calls") or []
        tool_calls = [
            {
                "id": tc.get("id", ""),
                "type": "function",
                "function": {
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": tc.get("function", {}).get("arguments", "{}"),
                },
            }
            for tc in raw_tcs
        ]

        return {
            "content": message.get("content") or "",
            "tool_calls": tool_calls,
            "latency_ms": elapsed_ms,
            "eval_count": eval_count,
            "tok_per_s": round(eval_count / max(elapsed_ms / 1000, 0.001), 1),
            "raw": data,
        }

    def close(self):
        self._client.close()
