"""Tool definitions shared across scenarios — mirror of Aurelia and Hermes real tools."""
from abs.scenario import ToolDef

HEALTH_CHECK = ToolDef(
    name="health_check",
    description="Verifica saúde da máquina: CPU, RAM, GPU, disco, serviços Docker e systemd.",
    parameters={
        "type": "object",
        "properties": {
            "detail_level": {
                "type": "string",
                "enum": ["summary", "full"],
                "description": "Nível de detalhe do relatório",
            }
        },
        "required": [],
    },
)

ANALYZE_URL = ToolDef(
    name="analyze_url",
    description="Busca e analisa o conteúdo de uma URL, retornando resumo e relevância técnica.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL completa a ser analisada"}
        },
        "required": ["url"],
    },
)

YOUTUBE_TRANSCRIPT = ToolDef(
    name="youtube_transcript",
    description="Obtém a transcrição de um vídeo do YouTube a partir da URL.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL do vídeo no YouTube"}
        },
        "required": ["url"],
    },
)

CRON_CREATE = ToolDef(
    name="cron_create",
    description="Cria um job cron agendado para execução recorrente.",
    parameters={
        "type": "object",
        "properties": {
            "schedule": {"type": "string", "description": "Expressão cron (ex: '0 2 * * *')"},
            "command": {"type": "string", "description": "Comando shell a executar"},
            "description": {"type": "string", "description": "Descrição do job"},
        },
        "required": ["schedule", "command"],
    },
)

FILE_READ = ToolDef(
    name="file_read",
    description="Lê o conteúdo de um arquivo no servidor.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Caminho absoluto do arquivo"},
        },
        "required": ["path"],
    },
)

SHELL_EXEC = ToolDef(
    name="shell_exec",
    description="Executa um comando shell no servidor e retorna stdout e stderr.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Comando shell a executar"},
        },
        "required": ["command"],
    },
)

# Convenience groupings
AURELIA_TOOLS = [HEALTH_CHECK, ANALYZE_URL, YOUTUBE_TRANSCRIPT]
HERMES_TOOLS = [HEALTH_CHECK, SHELL_EXEC, FILE_READ, CRON_CREATE, ANALYZE_URL]
ALL_TOOLS = [HEALTH_CHECK, ANALYZE_URL, YOUTUBE_TRANSCRIPT, CRON_CREATE, FILE_READ, SHELL_EXEC]
