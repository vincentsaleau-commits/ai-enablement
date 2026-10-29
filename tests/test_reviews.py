import json

import pytest

from support_triage.reviews import record_review


@pytest.fixture
def export_path(tmp_path):
    path = tmp_path / "tickets.csv"
    path.write_text(
        "id,status,subject\nT-1,open,Withdrawal pending\nT-2,solved,Bonus question\n",
        encoding="utf-8",
    )
    return path


def test_review_is_marked_unverified_caller_submission(export_path, tmp_path):
    log_path = tmp_path / "review" / "decisions.jsonl"

    decision = record_review(
        export_path,
        log_path,
        "T-1",
        "withdrawal",
        "needs_policy_review",
        "Check the applicable withdrawal terms.",
        "Mai",
    )

    assert decision["record_type"] == "caller_submitted_triage"
    assert decision["review_status"] == "unverified"
    assert "human_confirmed" not in decision


def test_review_appends_auditable_decision_without_changing_export(export_path, tmp_path):
    log_path = tmp_path / "review" / "decisions.jsonl"
    original_export = export_path.read_bytes()

    decision = record_review(
        export_path,
        log_path,
        "T-1",
        "withdrawal",
        "needs_policy_review",
        "Check the applicable withdrawal terms.",
        "Mai",
    )

    logged = json.loads(log_path.read_text(encoding="utf-8"))
    assert logged == decision
    assert decision["review_status"] == "unverified"
    assert decision["ticket_id"] == "T-1"
    assert export_path.read_bytes() == original_export


def test_review_rejects_unknown_ticket(export_path, tmp_path):
    with pytest.raises(ValueError, match="not found"):
        record_review(
            export_path,
            tmp_path / "decisions.jsonl",
            "missing",
            "withdrawal",
            "needs_policy_review",
            "Check the applicable withdrawal terms.",
            "Mai",
        )