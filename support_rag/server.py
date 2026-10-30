import logging
import os
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from support_rag.engine import run_batch
from support_rag.ollama import OllamaClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
mcp = MCPServer("local-support-rag")


@mcp.tool()
def run_local_rag_triage() -> dict[str, Any]:
    """Triage all open tickets with local Ollama RAG and save unverified suggestions locally.

    Ticket text and generated drafts stay on this machine. Only counts, model names,
    and the output path are returned to the MCP client.
    """
    export_value = os.environ.get("SUPPORT_EXPORT_PATH")
    if not export_value:
        raise ToolError("Set SUPPORT_EXPORT_PATH to a local JSON ticket export")

    export_path = Path(export_value).expanduser()
    knowledge_dir = Path(
        os.environ.get("SUPPORT_KNOWLEDGE_DIR", str(export_path.parent))
    ).expanduser()
    output_path = Path(
        os.environ.get(
            "SUPPORT_RAG_OUTPUT_PATH",
            str(Path(__file__).resolve().parents[1] / "review" / "triage_suggestions.jsonl"),
        )
    ).expanduser()
    client = OllamaClient(
        embedding_model=os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        generation_model=os.environ.get("OLLAMA_GENERATION_MODEL", "qwen2.5:3b"),
    )
    try:
        result = run_batch(export_path, knowledge_dir, output_path, client)
    except (OSError, RuntimeError, ValueError) as error:
        logger.error("Local RAG triage failed: %s", error)
        raise ToolError(str(error)) from error
    return {
        **result,
        "embedding_model": client.embedding_model,
        "generation_model": client.generation_model,
        "ticket_content_returned": False,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")