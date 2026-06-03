"""Q-series — Quality scenarios, no tools. Tests reasoning, format, and multi-turn coherence."""
from abs.scenario import Scenario, Turn, ScoreSpec

Q_SERIES: list[Scenario] = [
    Scenario(
        id="Q1",
        series="Q",
        name="Raciocínio técnico — trade-offs de hardware LLM",
        description="Avalia raciocínio sobre trade-offs reais de hardware para LLMs locais.",
        turns=[
            Turn(role="user", content=(
                "Tenho um servidor com RTX 3060 12GB e estou considerando comprar uma RTX 4090 24GB "
                "para melhorar a qualidade dos meus agentes de IA locais. "
                "Vale a pena o investimento considerando que uso modelos entre 7B e 9B parâmetros? "
                "Seja direto e técnico."
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["suficiente", "não vale", "custo", "velocidade", "12gb", "qualidade"],
        ),
        tags=["reasoning", "hardware"],
    ),
    Scenario(
        id="Q2",
        series="Q",
        name="Conformidade de formato JSON",
        description="Avalia se o modelo retorna JSON válido e completo quando solicitado.",
        turns=[
            Turn(role="user", content=(
                "Retorne APENAS um JSON (sem markdown, sem explicação) com as seguintes informações "
                "sobre o modelo gemma4:e4b: "
                '{"model_name": ..., "params_billions": ..., "vram_gb": ..., "use_case": ...}'
            )),
        ],
        score_spec=ScoreSpec(
            method="json_schema",
            required_keys=["model_name", "params_billions", "vram_gb", "use_case"],
        ),
        tags=["format", "json"],
    ),
    Scenario(
        id="Q2v2",
        series="Q",
        name="Conformidade de formato JSON — dados fornecidos",
        description=(
            "Avalia se o modelo retorna JSON válido e completo quando os dados são fornecidos no prompt. "
            "Versão neutra do Q2: elimina dependência de knowledge cutoff sobre modelos específicos."
        ),
        turns=[
            Turn(role="user", content=(
                "Os dados abaixo descrevem um modelo de linguagem. "
                "Retorne APENAS um JSON (sem markdown, sem explicação) com exatamente estas chaves:\n"
                '{"model_name": ..., "params_billions": ..., "vram_gb": ..., "use_case": ...}\n\n'
                "Dados: nome=atlas-7b, parâmetros=7 bilhões, VRAM necessária=5.2GB, uso=chat e código."
            )),
        ],
        score_spec=ScoreSpec(
            method="json_schema",
            required_keys=["model_name", "params_billions", "vram_gb", "use_case"],
        ),
        tags=["format", "json"],
    ),
    Scenario(
        id="Q3",
        series="Q",
        name="Retenção de contexto em conversa técnica",
        description="Avalia se o modelo mantém contexto ao longo de 4 turns.",
        turns=[
            Turn(role="user", content="Estou testando o modelo gemma4:e4b no meu servidor. Ele usa cerca de 9.6GB de VRAM."),
            Turn(role="assistant", content="Entendido. O gemma4:e4b com quantização Q4 ocupa aproximadamente 9.6GB de VRAM, deixando margem confortável numa RTX 3060 12GB."),
            Turn(role="user", content="Meu servidor tem duas RTX 3060. Quanto de VRAM total tenho disponível?"),
            Turn(role="assistant", content="Com duas RTX 3060 12GB você tem 24GB de VRAM total, distribuídos em dois bancos de 12GB cada."),
            Turn(role="user", content="Quantas instâncias do modelo que eu mencionei eu poderia rodar simultaneamente, uma em cada GPU?"),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["duas", "2", "e4b", "gpu", "simultane"],
        ),
        tags=["multi-turn", "context"],
    ),
    Scenario(
        id="Q4",
        series="Q",
        name="Análise de log de erro — diagnóstico",
        description="Avalia capacidade de diagnóstico a partir de um log real.",
        turns=[
            Turn(role="user", content=(
                "Analise esse trecho de log e diga o que está acontecendo e qual a causa provável:\n\n"
                "ERRO: [ollama] failed to load model gemma4:26b-a4b-it-q4_K_M\n"
                "CUDA error: out of memory (error 2)\n"
                "VRAM requested: 17421MB, available: 12288MB\n"
                "Suggestion: try a smaller model or reduce context window"
            )),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["vram", "memória", "12", "17", "insuficiente", "menor"],
        ),
        tags=["reasoning", "logs", "diagnostics"],
    ),
]
