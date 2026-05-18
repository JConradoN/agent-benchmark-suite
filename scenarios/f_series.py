"""F-series — Framework scenarios. Run through real Aurelia/Hermes agents (no mock tools).

Unlike other series (Ollama direct + mock injection), F-series lets each framework
execute tools natively. Scenarios are designed to test tasks that both agents support
with their own built-in capabilities.

Tags: "aurelia" | "hermes" | "both" — which framework(s) make sense for each scenario.
"""
from abs.scenario import Scenario, Turn, ScoreSpec

F_SERIES: list[Scenario] = [
    # --- No-tool quality tests (directly comparable across frameworks) ---
    Scenario(
        id="F1",
        series="F",
        name="Raciocínio técnico — modelo para RTX 3060 12GB",
        description="Sem tools. Avalia raciocínio comparável ao Q1/Q3 mas no contexto do framework real.",
        turns=[
            Turn(role="user", content=(
                "Tenho uma RTX 3060 12GB e quero rodar um agente de IA local eficiente. "
                "Qual modelo você recomenda entre gemma4:e4b e gemma4:26b? "
                "Responda em 3 linhas objetivas."
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["e4b", "eficiente", "vram", "9", "12"],
        ),
        tags=["framework", "both", "reasoning"],
    ),
    Scenario(
        id="F2",
        series="F",
        name="Conformidade de formato JSON — no framework",
        description="Sem tools. Avalia se o framework preserva instrução de formato JSON.",
        turns=[
            Turn(role="user", content=(
                "Retorne APENAS um JSON (sem markdown, sem explicação) com campos: "
                '{"model": "...", "vram_gb": ..., "use_case": "..."} '
                "para o modelo gemma4:e4b."
            )),
        ],
        score_spec=ScoreSpec(
            method="json_schema",
            required_keys=["model", "vram_gb", "use_case"],
        ),
        tags=["framework", "both", "format"],
    ),
    Scenario(
        id="F3",
        series="F",
        name="Retenção multi-turn — contexto técnico no framework",
        description="4 turns sem tools. Avalia retenção de contexto dentro do framework (sessão real).",
        turns=[
            Turn(role="user", content="Meu servidor tem duas RTX 3060 12GB. Total de 24GB de VRAM."),
            Turn(role="assistant", content="Entendido. Duas RTX 3060 12GB, total 24GB de VRAM distribuídos em dois bancos independentes."),
            Turn(role="user", content="Estou rodando gemma4:e4b em uma delas. Usa ~9.6GB de VRAM."),
            Turn(role="assistant", content="Com gemma4:e4b usando 9.6GB na primeira GPU, sobram 2.4GB nessa GPU e 12GB livres na segunda."),
            Turn(role="user", content="Quanto de VRAM total ainda tenho disponível para rodar um segundo modelo?"),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["14", "12", "segunda", "gpu", "disponível"],
        ),
        tags=["framework", "both", "multi-turn", "retention"],
    ),
    # --- Tool-use tests (each framework uses its real tools) ---
    Scenario(
        id="F4",
        series="F",
        name="Shell — listar containers Docker em execução",
        description="Hermes usa shell_exec real. Aurelia usa health_check ou bridge. Avalia se obtém contagem correta.",
        turns=[
            Turn(role="user", content=(
                "Liste os containers Docker que estão rodando agora e me diga quantos são."
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["container", "docker", "rodando"],
        ),
        tags=["framework", "both", "shell", "tools"],
    ),
    Scenario(
        id="F5",
        series="F",
        name="Diagnóstico — verificar saúde do servidor",
        description="Cada framework usa suas tools nativas (health_check, shell_exec, etc.) para diagnosticar o servidor.",
        turns=[
            Turn(role="user", content=(
                "O servidor está apresentando lentidão. Verifique o estado atual "
                "do sistema e me diga o que está acontecendo."
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["cpu", "ram", "memória", "processo"],
        ),
        tags=["framework", "both", "diagnostics", "tools"],
    ),
    Scenario(
        id="F6",
        series="F",
        name="Leitura de arquivo — conteúdo de configuração",
        description="Hermes usa file_read real. Avalia leitura e interpretação de arquivo do sistema.",
        turns=[
            Turn(role="user", content=(
                "Leia o arquivo /etc/os-release e me diz qual é o sistema operacional e versão."
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["ubuntu", "linux", "versão", "26"],
        ),
        tags=["framework", "hermes", "file", "tools"],
    ),
    Scenario(
        id="F7",
        series="F",
        name="Análise de URL — fox-server dashboard",
        description="Aurelia e Hermes analisam URL interna real. Avalia se conseguem acessar e resumir.",
        turns=[
            Turn(role="user", content=(
                "Analisa http://fox-server.lan/home/ e me diz o que está nessa página."
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["fox", "servidor", "painel", "serviço"],
        ),
        tags=["framework", "both", "url", "tools"],
    ),
]
