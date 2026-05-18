"""T-series — Single tool scenarios. Tests correct tool selection and parameter precision."""
from abs.scenario import Scenario, Turn, ScoreSpec
from scenarios.tools import AURELIA_TOOLS, HERMES_TOOLS, ALL_TOOLS, ANALYZE_URL, HEALTH_CHECK, YOUTUBE_TRANSCRIPT, CRON_CREATE

T_SERIES: list[Scenario] = [
    Scenario(
        id="T1",
        series="T",
        name="Seleção de tool — URL analysis",
        description="Deve chamar analyze_url com a URL correta ao receber pedido de análise de link.",
        turns=[
            Turn(role="user", content="Analisa essa URL pra mim: https://ollama.com/blog/gemma3"),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="tool_call",
            expected_tool="analyze_url",
            expected_params={"url": "https://ollama.com/blog/gemma3"},
        ),
        mock_tool_responses={
            "analyze_url": '{"title": "Gemma3 on Ollama", "summary": "Post about Gemma3 model availability", "relevant": true}'
        },
        tags=["tool-selection", "aurelia"],
    ),
    Scenario(
        id="T2",
        series="T",
        name="Seleção de tool — YouTube transcript",
        description="Deve chamar youtube_transcript quando receber URL do YouTube.",
        turns=[
            Turn(role="user", content="Consegue pegar a transcrição desse vídeo? https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="tool_call",
            expected_tool="youtube_transcript",
            expected_params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        ),
        mock_tool_responses={
            "youtube_transcript": '{"transcript": "We\'re no strangers to love...", "duration_seconds": 212}'
        },
        tags=["tool-selection", "aurelia"],
    ),
    Scenario(
        id="T3",
        series="T",
        name="Seleção de tool — health check",
        description="Deve chamar health_check quando perguntado sobre saúde do servidor.",
        turns=[
            Turn(role="user", content="Como está o servidor? Quero ver CPU, RAM e GPU."),
        ],
        tools=AURELIA_TOOLS,
        score_spec=ScoreSpec(
            method="tool_call",
            expected_tool="health_check",
            expected_params={},
        ),
        mock_tool_responses={
            "health_check": '{"cpu_pct": 12, "ram_used_gb": 45, "ram_total_gb": 128, "gpu0_vram_used_gb": 9.6, "gpu0_vram_total_gb": 12}'
        },
        tags=["tool-selection", "aurelia"],
    ),
    Scenario(
        id="T4",
        series="T",
        name="Precisão de parâmetro — URL com query string",
        description="Avalia se a URL completa (com query string) é extraída corretamente.",
        turns=[
            Turn(role="user", content="Analisa: https://github.com/search?q=ollama+agent&type=repositories"),
        ],
        tools=[ANALYZE_URL],
        score_spec=ScoreSpec(
            method="tool_call",
            expected_tool="analyze_url",
            expected_params={"url": "https://github.com/search?q=ollama+agent&type=repositories"},
        ),
        mock_tool_responses={
            "analyze_url": '{"title": "GitHub Search", "results": 142}'
        },
        tags=["tool-params", "url-extraction"],
    ),
    Scenario(
        id="T5",
        series="T",
        name="Seleção de tool — cron scheduling (Hermes)",
        description="Deve chamar cron_create com schedule e command corretos.",
        turns=[
            Turn(role="user", content="Agenda um backup do /mnt/vault todo dia às 3h da manhã usando o comando 'rsync -av /mnt/vault /backup/vault'."),
        ],
        tools=HERMES_TOOLS,
        score_spec=ScoreSpec(
            method="tool_call",
            expected_tool="cron_create",
            expected_params={"schedule": "0 3 * * *", "command": "rsync"},
        ),
        mock_tool_responses={
            "cron_create": '{"job_id": "vault-backup-001", "created": true, "next_run": "03:00"}'
        },
        tags=["tool-selection", "hermes", "cron"],
    ),
    Scenario(
        id="T6",
        series="T",
        name="Discriminação de tool — URL vs YouTube",
        description="Com todas as tools disponíveis, deve distinguir URL YouTube de URL genérica.",
        turns=[
            Turn(role="user", content="https://www.youtube.com/watch?v=abc123 — consegue transcrever?"),
        ],
        tools=ALL_TOOLS,
        score_spec=ScoreSpec(
            method="tool_call",
            expected_tool="youtube_transcript",
            expected_params={"url": "https://www.youtube.com/watch?v=abc123"},
        ),
        mock_tool_responses={
            "youtube_transcript": '{"transcript": "Conteúdo do vídeo...", "duration_seconds": 600}'
        },
        tags=["tool-discrimination", "aurelia"],
    ),
]
