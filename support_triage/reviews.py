import json
from datetime import datetime, timezone
from pathlib import Path

from support_triage.data import load_tickets


CATEGORIES = {"withdrawal", "bonus", "deposit", "account_access", "other"}
DISPOSITIONS = {"needs_policy_review", "process_issue", "policy_confirmed", "not_relevant"}


def record_review(
    export_path: str | Path,
    log_path: str | Path,
    ticket_id: str,
    category: str,
    disposition: str,
    rationale: str,
    reviewer: str,
) -> dict[str, str]:
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of: {', '.join(sorted(CATEGORIES))}")
    if disposition not in DISPOSITIONS:
        raise ValueError(f"disposition must be one of: {', '.join(sorted(DISPOSITIONS))}")
    if len(rationale.strip()) < 10:
        raise ValueError("rationale must contain at least 10 non-whitespace characters")
    if not reviewer.strip():
        raise ValueError("reviewer is required")

    tickets = load_tickets(export_path, open_only=False)
    if not any(ticket["id"] == ticket_id for ticket in tickets):
        raise ValueError(f"Ticket ID not found in export: {ticket_id}")

    # The reviewer name and confirmation are caller-submitted and not verified
    # by this tool. The record is an audit note, not proof of human approval.
    review = {
        "record_type": "caller_submitted_triage",
        "review_status": "unverified",
        "ticket_id": ticket_id,
        "category": category,
        "disposition": disposition,
        "rationale": rationale.strip(),
        "reviewer": reviewer.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    destination = Path(log_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(review, ensure_ascii=True) + "\n")
    return review