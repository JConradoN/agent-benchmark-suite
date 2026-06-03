from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    base_url: str = "http://localhost:11434"
    model: str = "gemma4:e4b-it-q4_K_M"
    timeout: int = 120
    think: bool = False
    temperature: float = 0.0


@dataclass
class RunConfig:
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    runs_per_scenario: int = 3
    output_dir: str = "results"
    series: list[str] = field(default_factory=lambda: ["Q", "T", "C", "L", "M"])
    verbose: bool = False
    no_think_prefix: bool = False   # H1: injeta /no_think no system prompt
    grounding_prefix: bool = False  # H2: injeta instrução anti-alucinação no system prompt
