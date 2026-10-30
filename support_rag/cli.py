import argparse
import os
import sys
from pathlib import Path

from support_rag.engine import run_batch
from support_rag.ollama import OllamaClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local Ollama RAG over open support tickets")
    parser.add_argument("--export", default=os.environ.get("SUPPORT_EXPORT_PATH"))
    parser.add_argument("--knowledge-dir", default=os.environ.get("SUPPORT_KNOWLEDGE_DIR"))
    parser.add_argument(
        "--output",
        default=os.environ.get(
            "SUPPORT_RAG_OUTPUT_PATH",
            str(Path(__file__).resolve().parents[1] / "review" / "triage_suggestions.jsonl"),
        ),
    )
    args = parser.parse_args()
    if not args.export:
        parser.error("--export or SUPPORT_EXPORT_PATH is required")

    export_path = Path(args.export).expanduser()
    knowledge_dir = Path(args.knowledge_dir).expanduser() if args.knowledge_dir else export_path.parent
    client = OllamaClient(
        embedding_model=os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        generation_model=os.environ.get("OLLAMA_GENERATION_MODEL", "qwen2.5:3b"),
    )
    try:
        result = run_batch(export_path, knowledge_dir, args.output, client)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"RAG run failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Processed {result['processed']} open tickets; suggestions are unverified. "
        f"Local output: {result['output_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())