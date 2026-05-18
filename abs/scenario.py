from dataclasses import dataclass, field
from typing import Any, Literal

Series = Literal["Q", "T", "C", "L", "M"]
ScoringMethod = Literal["keyword_match", "json_schema", "tool_call", "llm_judge", "automatic"]


@dataclass
class Turn:
    role: Literal["user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]

    def to_api(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ScoreSpec:
    """What to check and how to score it (0–4)."""
    method: ScoringMethod
    # keyword_match
    keywords: list[str] = field(default_factory=list)
    # tool_call
    expected_tool: str | None = None
    expected_params: dict[str, Any] = field(default_factory=dict)
    # json_schema
    required_keys: list[str] = field(default_factory=list)
    # llm_judge prompt
    judge_prompt: str | None = None


@dataclass
class Scenario:
    id: str
    series: Series
    name: str
    description: str
    turns: list[Turn]
    score_spec: ScoreSpec
    tools: list[ToolDef] = field(default_factory=list)
    # For chain/multi-turn: inject mock tool responses after the model calls a tool
    # str = single response; list[str] = rotates on successive calls to same tool
    mock_tool_responses: dict[str, str | list[str]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
