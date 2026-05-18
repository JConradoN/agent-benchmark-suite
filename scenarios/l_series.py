"""L-series — Long context scenarios. Tests context retention across many turns."""
from abs.scenario import Scenario, Turn, ScoreSpec

L_SERIES: list[Scenario] = [
    Scenario(
        id="L1",
        series="L",
        name="Retenção — informação introduzida no turn 1, perguntada no turn 5",
        description="Avalia se o modelo lembra de dado específico mencionado no início.",
        turns=[
            Turn(role="user", content="Meu servidor tem 128GB de RAM DDR4 ECC e um Xeon E5-2696 v3."),
            Turn(role="assistant", content="Entendido. Xeon E5-2696 v3 com 128GB DDR4 ECC — excelente configuração para workloads pesados."),
            Turn(role="user", content="Estou rodando dois containers Ollama, cada um usando cerca de 17GB de RAM."),
            Turn(role="assistant", content="Com dois containers usando 17GB cada, você está usando 34GB dos 128GB disponíveis — bastante margem."),
            Turn(role="user", content="Adicionei mais 3 containers de serviços que usam ~2GB cada."),
            Turn(role="assistant", content="Agora está em 34 + 6 = 40GB usados de 128GB total. Ainda 88GB livres."),
            Turn(role="user", content="Quanto de RAM total o meu servidor tem mesmo?"),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["128", "gb"],
        ),
        tags=["long-context", "retention", "turn-1"],
    ),
    Scenario(
        id="L2",
        series="L",
        name="Retenção — consistência numérica ao longo de 8 turns",
        description="Avalia se cálculos acumulativos permanecem consistentes.",
        turns=[
            Turn(role="user", content="Tenho um orçamento de €1.000 para hardware."),
            Turn(role="assistant", content="Ok, €1.000 de orçamento. Como posso ajudar a planejar?"),
            Turn(role="user", content="Quero gastar €350 em uma RTX 3060."),
            Turn(role="assistant", content="RTX 3060 por €350. Restam €650 do orçamento."),
            Turn(role="user", content="Mais €200 em 32GB de RAM DDR4."),
            Turn(role="assistant", content="RAM DDR4 por €200. Restam €450."),
            Turn(role="user", content="E €180 em um NVMe 1TB."),
            Turn(role="assistant", content="NVMe 1TB por €180. Restam €270."),
            Turn(role="user", content="Quanto sobrou do meu orçamento original?"),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["270", "€270"],
        ),
        tags=["long-context", "arithmetic", "budget"],
    ),
    Scenario(
        id="L3",
        series="L",
        name="Degradação de qualidade — resposta coerente após 10 turns",
        description="Avalia se a qualidade de resposta permanece alta após longa conversa.",
        turns=[
            Turn(role="user", content="Vou fazer algumas perguntas técnicas sobre LLMs."),
            Turn(role="assistant", content="Pode perguntar, estou pronto."),
            Turn(role="user", content="O que é quantização de modelos?"),
            Turn(role="assistant", content="Quantização reduz a precisão dos pesos do modelo (ex: float32 → int4), diminuindo uso de memória e aumentando velocidade de inferência com impacto mínimo na qualidade."),
            Turn(role="user", content="Quais são os formatos mais comuns?"),
            Turn(role="assistant", content="Os formatos mais comuns são GGUF (llama.cpp/Ollama), GPTQ (GPU), e AWQ (GPU otimizado). Para uso local com Ollama, GGUF Q4_K_M é o padrão recomendado."),
            Turn(role="user", content="O que é MoE?"),
            Turn(role="assistant", content="Mixture of Experts: arquitetura onde o modelo tem múltiplos 'especialistas' (sub-redes), mas apenas alguns são ativados por token. Permite modelos grandes com custo computacional de modelos menores."),
            Turn(role="user", content="Exemplo de modelo MoE?"),
            Turn(role="assistant", content="Exemplos: Mixtral 8x7B (8 especialistas, 2 ativos), Gemma4 26B a4b (4B parâmetros ativos de 26B total), GLM-4.7-Flash (30B-A3B)."),
            Turn(role="user", content="Qual o modelo mais eficiente para agentes locais com RTX 3060 12GB?"),
        ],
        score_spec=ScoreSpec(
            method="keyword_match",
            keywords=["e4b", "gemma4", "12gb", "eficiente"],
        ),
        tags=["long-context", "quality-degradation", "technical"],
    ),
]
