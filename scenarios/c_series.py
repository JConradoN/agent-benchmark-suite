"""C-series — Chain scenarios. Tests sequential multi-tool use and result interpretation."""
from abs.scenario import Scenario, Turn, ScoreSpec
from scenarios.tools import AURELIA_TOOLS, HERMES_TOOLS, ALL_TOOLS

C_SERIES: list[Scenario] = [
    Scenario(
        id="C1",
        series="C",
        name="Chain — URL analysis → resumo final",
        description="Analisa URL, recebe resultado, produz resumo estruturado. 1 tool, 2 turnos de raciocínio.",
        turns=[
            Turn(role="user", content=(
                "Analisa a URL https://arxiv.org/abs/2305.10601 e me diz: "
                "1) do que trata o paper, 2) se é relevante para uso de LLMs em agentes locais."
            )),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["paper", "relevante", "agente", "llm"],
        ),
        mock_tool_responses={
            "analyze_url": (
                '{"title": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models", '
                '"abstract": "Introduces Tree of Thoughts framework for LLM reasoning via deliberate search.", '
                '"year": 2023, "relevant_to_agents": true}'
            )
        },
        tags=["chain", "aurelia", "interpretation"],
    ),
    Scenario(
        id="C2",
        series="C",
        name="Chain — health check → diagnóstico → recomendação",
        description="Verifica saúde, interpreta resultado crítico, recomenda ação. 1 tool + raciocínio.",
        turns=[
            Turn(role="user", content="O servidor está lento. Verifica o que está acontecendo e me diz o que fazer."),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["ram", "memória", "90", "processo", "reinici"],
        ),
        mock_tool_responses={
            "health_check": (
                '{"cpu_pct": 8, "ram_used_gb": 118, "ram_total_gb": 128, "ram_pct": 92, '
                '"gpu0_vram_used_gb": 9.6, "gpu0_vram_total_gb": 12, '
                '"top_processes": [{"name": "ollama", "ram_gb": 17}, {"name": "n8n", "ram_gb": 4}]}'
            )
        },
        tags=["chain", "aurelia", "diagnostics"],
    ),
    Scenario(
        id="C3",
        series="C",
        name="Chain — 2 tool calls sequenciais (comparação de URLs)",
        description="Analisa duas URLs separadas e produz comparação. Exige 2 chamadas à mesma tool.",
        turns=[
            Turn(role="user", content=(
                "Compara esses dois projetos para mim: "
                "https://github.com/ollama/ollama e https://github.com/vllm-project/vllm. "
                "Qual é mais adequado para homelab com uma GPU consumer?"
            )),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["ollama", "vllm", "consumer", "homelab", "simpl"],
        ),
        mock_tool_responses={
            "analyze_url": (
                '{"title": "Ollama", "description": "Run LLMs locally, simple setup, supports consumer GPUs", '
                '"stars": 85000, "language": "Go"}'
            )
        },
        tags=["chain", "multi-call", "comparison"],
    ),
    Scenario(
        id="C4",
        series="C",
        name="Chain — shell exec → interpretação de resultado (Hermes)",
        description="Executa comando, interpreta saída, responde com base nos dados reais.",
        turns=[
            Turn(role="user", content="Quantos containers Docker estão rodando agora?"),
        ],
        tools=HERMES_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["9", "nove", "container", "rodando", "ativo"],
        ),
        mock_tool_responses={
            "shell_exec": (
                '{"stdout": "qdrant\\nn8n\\nlitellm\\nfortejus-api\\nollama\\nopen-webui\\nsearxng\\nfox-noc\\nportainer\\n", '
                '"returncode": 0}'
            )
        },
        tags=["chain", "hermes", "shell"],
    ),
    Scenario(
        id="C5",
        series="C",
        name="Chain — tool loop detection (não deve fazer loop)",
        description="Recebe resposta de tool que implica nova ação, mas deve saber quando parar.",
        turns=[
            Turn(role="user", content="Verifica a saúde do servidor e me dá um resumo em 3 linhas."),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["cpu", "ram", "gpu"],
        ),
        mock_tool_responses={
            "health_check": (
                '{"cpu_pct": 15, "ram_used_gb": 48, "ram_total_gb": 128, '
                '"gpu0_vram_used_gb": 9.6, "gpu0_vram_total_gb": 12, "status": "healthy"}'
            )
        },
        tags=["chain", "loop-detection", "aurelia"],
    ),
]
