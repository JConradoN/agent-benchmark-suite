import pytest
from abs.scorer import (
    _score_keywords,
    _score_json_schema,
    _score_tool_call,
    _score_latency,
)
from abs.scenario import ScoreSpec


def test_keyword_all_present():
    assert _score_keywords("O modelo usa 9.6GB de VRAM com RTX 3060", ["vram", "rtx"]) == 4


def test_keyword_partial():
    assert _score_keywords("O modelo usa 9.6GB de VRAM", ["vram", "rtx", "gemma", "gpu"]) == 1


def test_keyword_none():
    assert _score_keywords("Resposta completamente irrelevante aqui", ["vram", "rtx"]) == 0


def test_keyword_empty_list():
    assert _score_keywords("qualquer coisa", []) == 4


def test_json_valid_all_keys():
    content = '{"model_name": "gemma4", "params_billions": 9.7, "vram_gb": 9.6, "use_case": "agents"}'
    assert _score_json_schema(content, ["model_name", "params_billions", "vram_gb", "use_case"]) == 4


def test_json_with_markdown_fence():
    content = '```json\n{"model_name": "e4b", "vram_gb": 9.6}\n```'
    assert _score_json_schema(content, ["model_name", "vram_gb"]) == 4


def test_json_invalid():
    assert _score_json_schema("Aqui está o JSON: blah blah", ["model_name"]) == 0


def test_json_partial_keys():
    content = '{"model_name": "gemma4", "vram_gb": 9.6}'
    assert _score_json_schema(content, ["model_name", "vram_gb", "missing_key"]) == 2


def test_tool_call_correct_tool_and_params():
    tool_calls = [{"function": {"name": "analyze_url", "arguments": {"url": "https://ollama.com"}}}]
    spec = ScoreSpec(method="tool_call", expected_tool="analyze_url", expected_params={"url": "https://ollama.com"})
    assert _score_tool_call(tool_calls, spec) == 4


def test_tool_call_wrong_tool():
    tool_calls = [{"function": {"name": "health_check", "arguments": {}}}]
    spec = ScoreSpec(method="tool_call", expected_tool="analyze_url", expected_params={"url": "x"})
    assert _score_tool_call(tool_calls, spec) == 1


def test_tool_call_no_calls():
    spec = ScoreSpec(method="tool_call", expected_tool="analyze_url", expected_params={"url": "x"})
    assert _score_tool_call([], spec) == 0


def test_latency_scores():
    assert _score_latency(1000) == 4
    assert _score_latency(5000) == 3
    assert _score_latency(15000) == 2
    assert _score_latency(30000) == 1
    assert _score_latency(120000) == 0
