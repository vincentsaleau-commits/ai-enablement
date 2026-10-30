
import pytest

from support_rag.evaluation import (
    evaluate_citations,
    load_jsonl,
    run_retrieval_evaluation,
    score_retrieval,
)


def test_score_retrieval_reports_recall_at_k_and_mean_reciprocal_rank() -> None:
    cases = [
        ({"support-handbook-v2.md"}, ["support-handbook-v2.md", "bonus-terms.md"]),
        ({"bonus-terms.md", "support-handbook-v2.md"}, ["finance-month-end-sept.md", "bonus-terms.md"]),
    ]

    result = score_retrieval(cases)

    assert result["recall_at_k"] == 0.67
    assert result["mrr"] == 0.75
    assert result["cases"] == 2


def test_evaluate_citations_rejects_missing_or_unknown_evidence_ids() -> None:
    records = [
        {
            "abstain": False,
            "citations": ["E1"],
            "retrieved_evidence": [{"evidence_id": "E1", "source": "support-handbook-v2.md"}],
            "draft_reply": "We are checking this.",
        },
        {
            "abstain": False,
            "citations": ["E9"],
            "retrieved_evidence": [{"evidence_id": "E1", "source": "bonus-terms.md"}],
            "draft_reply": "Unsupported answer.",
        },
        {
            "abstain": True,
            "citations": [],
            "retrieved_evidence": [{"evidence_id": "E1", "source": "bonus-terms.md"}],
            "draft_reply": "",
        },
    ]

    result = evaluate_citations(records)

    assert result["records"] == 3
    assert result["valid_records"] == 2
    assert result["invalid_records"] == 1
    assert result["citation_valid_rate"] == 0.67


def test_run_retrieval_evaluation_uses_golden_queries(tmp_path) -> None:
    (tmp_path / "support-handbook-v2.md").write_text("withdrawal refund 24 hours", encoding="utf-8")
    (tmp_path / "bonus-terms.md").write_text("bonus slots table live", encoding="utf-8")
    (tmp_path / "finance-month-end-sept.md").write_text("QuickPay delayed withdrawals", encoding="utf-8")

    class FakeOllama:
        def embed(self, texts: list[str]) -> list[list[float]]:
            vectors = []
            for text in texts:
                lowered = text.lower()
                vectors.append(
                    [
                        float("withdrawal" in lowered or "refund" in lowered),
                        float("bonus" in lowered),
                        float("quickpay" in lowered),
                    ]
                )
            return vectors

    result = run_retrieval_evaluation(tmp_path, FakeOllama())

    # The QuickPay case relies on the finance file, which is no longer a policy source, so it cannot be recalled.
    assert result == {"cases": 4, "recall_at_k": 0.75, "mrr": 0.75}


def test_load_jsonl_rejects_invalid_lines(tmp_path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        load_jsonl(path)