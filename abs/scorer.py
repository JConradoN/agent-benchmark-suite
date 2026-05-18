import json
from abs.scenario import Scenario, ScoreSpec


def score_response(scenario: Scenario, response: dict) -> dict[str, int]:
    """Returns dimension scores (0–4) for a single run response."""
    spec = scenario.score_spec
    scores: dict[str, int] = {}

    if spec.method == "keyword_match":
        scores["QUAL"] = _score_keywords(response["content"], spec.keywords)

    elif spec.method == "json_schema":
        scores["QUAL"] = _score_json_schema(response["content"], spec.required_keys)

    elif spec.method == "tool_call":
        scores["TOOL"] = _score_tool_call(response["tool_calls"], spec)

    elif spec.method == "llm_judge":
        # Placeholder — will require a separate judge call
        scores["QUAL"] = -1

    scores["LAT"] = _score_latency(response["latency_ms"])
    return scores


def _score_keywords(content: str, keywords: list[str]) -> int:
    if not keywords:
        return 4
    content_lower = content.lower()
    hits = sum(1 for kw in keywords if kw.lower() in content_lower)
    ratio = hits / len(keywords)
    if ratio >= 1.0:
        return 4
    if ratio >= 0.75:
        return 3
    if ratio >= 0.5:
        return 2
    if ratio > 0:
        return 1
    return 0


def _score_json_schema(content: str, required_keys: list[str]) -> int:
    # Strip markdown code fences if present
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON block inside text
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            return 0
        try:
            data = json.loads(content[start:end])
        except json.JSONDecodeError:
            return 0

    if not required_keys:
        return 4

    hits = sum(1 for k in required_keys if k in data)
    ratio = hits / len(required_keys)
    if ratio >= 1.0:
        return 4
    if ratio >= 0.75:
        return 3
    if ratio >= 0.5:
        return 2
    if ratio > 0:
        return 1
    return 0


def _score_tool_call(tool_calls: list[dict], spec: ScoreSpec) -> int:
    if not tool_calls:
        return 0

    call = tool_calls[0]
    fn = call.get("function", {})
    called_name = fn.get("name", "")

    if called_name != spec.expected_tool:
        return 1  # attempted tool use but wrong tool

    if not spec.expected_params:
        return 4  # correct tool, no param check required

    try:
        args = fn.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
    except (json.JSONDecodeError, TypeError):
        return 2  # correct tool, unparseable params

    hits = sum(
        1 for k, v in spec.expected_params.items()
        if k in args and (v is None or str(v).lower() in str(args[k]).lower())
    )
    ratio = hits / len(spec.expected_params)
    if ratio >= 1.0:
        return 4
    if ratio >= 0.75:
        return 3
    if ratio >= 0.5:
        return 2
    return 2  # correct tool, but params wrong


def _score_latency(latency_ms: int) -> int:
    """Higher score = faster response."""
    if latency_ms < 3_000:
        return 4
    if latency_ms < 8_000:
        return 3
    if latency_ms < 20_000:
        return 2
    if latency_ms < 60_000:
        return 1
    return 0
