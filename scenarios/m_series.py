"""M-series — Multi-agent scenarios. Same task sent to Aurelia and Hermes for comparison."""
from abs.scenario import Scenario, Turn, ScoreSpec
from scenarios.tools import AURELIA_TOOLS, HERMES_TOOLS, ALL_TOOLS

# M-series scenarios run the same task on multiple agents/models.
# The runner compares results across agents.
# Tags: "aurelia" or "hermes" indicate which agent profile to use.

M_SERIES: list[Scenario] = [
    Scenario(
        id="M1-A",
        series="M",
        name="Roteamento de tarefa — URL analysis (Aurelia profile)",
        description="Envia tarefa de análise de URL para o perfil Aurelia e mede qualidade + latência.",
        turns=[
            Turn(role="user", content=(
                "Analisa https://huggingface.co/blog/gemma3 e resume em 3 bullets "
                "o que é relevante para quem roda modelos localmente."
            )),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["gemma", "local", "bullet", "relevante"],
        ),
        mock_tool_responses={
            "analyze_url": (
                '{"title": "Gemma 3 on Hugging Face", '
                '"summary": "Gemma 3 models range from 1B to 27B parameters, '
                'optimized for efficiency, support GGUF format for local inference", '
                '"local_inference": true}'
            )
        },
        tags=["multi-agent", "aurelia", "comparison"],
    ),
    Scenario(
        id="M1-H",
        series="M",
        name="Roteamento de tarefa — URL analysis (Hermes profile)",
        description="Mesma tarefa do M1-A, perfil Hermes. Compara com M1-A.",
        turns=[
            Turn(role="user", content=(
                "Analisa https://huggingface.co/blog/gemma3 e resume em 3 bullets "
                "o que é relevante para quem roda modelos localmente."
            )),
        ],
        tools=HERMES_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["gemma", "local", "bullet", "relevante"],
        ),
        mock_tool_responses={
            "analyze_url": (
                '{"title": "Gemma 3 on Hugging Face", '
                '"summary": "Gemma 3 models range from 1B to 27B parameters, '
                'optimized for efficiency, support GGUF format for local inference", '
                '"local_inference": true}'
            )
        },
        tags=["multi-agent", "hermes", "comparison"],
    ),
    Scenario(
        id="M2-A",
        series="M",
        name="Diagnóstico de sistema — Aurelia profile",
        description="Diagnóstico completo do servidor: Aurelia usa health_check.",
        turns=[
            Turn(role="user", content="O servidor está apresentando lentidão. Faz um diagnóstico completo e recomenda ação."),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["ram", "cpu", "diagnóstico", "recomend"],
        ),
        mock_tool_responses={
            "health_check": (
                '{"cpu_pct": 85, "ram_used_gb": 120, "ram_total_gb": 128, '
                '"gpu0_vram_used_gb": 11.8, "gpu0_vram_total_gb": 12, '
                '"top_processes": [{"name": "ollama", "ram_gb": 34}]}'
            )
        },
        tags=["multi-agent", "aurelia", "diagnostics"],
    ),
    Scenario(
        id="M2-H",
        series="M",
        name="Diagnóstico de sistema — Hermes profile",
        description="Mesmo diagnóstico do M2-A, Hermes usa shell_exec.",
        turns=[
            Turn(role="user", content="O servidor está apresentando lentidão. Faz um diagnóstico completo e recomenda ação."),
        ],
        tools=HERMES_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["ram", "cpu", "diagnóstico", "recomend"],
        ),
        mock_tool_responses={
            "shell_exec": (
                '{"stdout": "CPU: 85%\\nRAM: 120/128GB\\nGPU0 VRAM: 11.8/12GB\\nTop: ollama (34GB RAM)\\n", '
                '"returncode": 0}'
            )
        },
        tags=["multi-agent", "hermes", "diagnostics"],
    ),
]
