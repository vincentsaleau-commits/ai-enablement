import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from support_rag.engine import load_knowledge_chunks, rank_chunks
from support_rag.ollama import OllamaClient


GOLDEN_CASES = (
    ("withdrawal approval target and delivery time", {"support-handbook-v2.md"}),
    ("bonus wagering contribution for slots table games and live casino", {"bonus-terms.md"}),
    ("agent refund limit and required team lead approval", {"support-handbook-v2.md"}),
    ("QuickPay delayed withdrawals in the September incident", {"finance-month-end-sept.md"}),
)


def score_retrieval(
    cases: Sequence[tuple[set[str], Sequence[str]]],
) -> dict[str, int | float]:
    if not cases:
        raise ValueError("At least one retrieval evaluation case is required")
    expected_total = sum(len(expected) for expected, _ in cases)
    if not expected_total:
        raise ValueError("Evaluation cases must define expected sources")
    hits = 0
    reciprocal_ranks = []
    for expected, retrieved in cases:
        hits += len(expected.intersection(retrieved))
        first_match = next(
            (rank for rank, source in enumerate(retrieved, start=1) if source in expected),
            None,
        )
        reciprocal_ranks.append(0.0 if first_match is None else 1.0 / first_match)
    return {
        "cases": len(cases),
        "recall_at_k": round(hits / expected_total, 2),
        "mrr": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 2),
    }


def evaluate_citations(records: Sequence[dict[str, object]]) -> dict[str, int | float]:
    valid_records = 0
    for record in records:
        evidence = record.get("retrieved_evidence", [])
        citations = record.get("citations", [])
        abstain = record.get("abstain") is True
        draft = record.get("draft_reply", "")
        evidence_ids = {
            item.get("evidence_id")
            for item in evidence
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        } if isinstance(evidence, list) else set()
        citations_are_valid = (
            isinstance(citations, list)
            and all(isinstance(item, str) and item in evidence_ids for item in citations)
        )
        if abstain:
            record_is_valid = citations_are_valid and not str(draft).strip()
        else:
            record_is_valid = citations_are_valid and bool(citations) and bool(str(draft).strip())
        valid_records += int(record_is_valid)
    total = len(records)
    return {
        "records": total,
        "valid_records": valid_records,
        "invalid_records": total - valid_records,
        "citation_valid_rate": round(valid_records / total, 2) if total else 1.0,
    }


def run_retrieval_evaluation(knowledge_dir: str | Path, ollama: OllamaClient) -> dict[str, int | float]:
    chunks = load_knowledge_chunks(knowledge_dir)
    chunk_vectors = ollama.embed([chunk.text for chunk in chunks])
    query_vectors = ollama.embed([query for query, _ in GOLDEN_CASES])
    if len(chunk_vectors) != len(chunks) or len(query_vectors) != len(GOLDEN_CASES):
        raise ValueError("Ollama returned an unexpected number of evaluation embeddings")
    results = []
    for (query, expected_sources), query_vector in zip(GOLDEN_CASES, query_vectors, strict=True):
        retrieved = rank_chunks(query_vector, chunks, chunk_vectors, limit=3)
        results.append((expected_sources, [chunk.source for chunk in retrieved]))
    return score_retrieval(results)


def load_jsonl(path: str | Path) -> list[dict[str, object]]:
    records = []
    with Path(path).expanduser().open("r", encoding="utf-8") as jsonl_file:
        for line_number, line in enumerate(jsonl_file, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at line {line_number}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected a JSON object at line {line_number}")
            records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local RAG retrieval and output citations")
    parser.add_argument("--knowledge-dir", required=True)
    parser.add_argument("--output", help="Optional local triage JSONL to evaluate")
    args = parser.parse_args()
    try:
        client = OllamaClient()
        report: dict[str, object] = {
            "retrieval": run_retrieval_evaluation(args.knowledge_dir, client)
        }
        if args.output:
            report["citations"] = evaluate_citations(load_jsonl(args.output))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())