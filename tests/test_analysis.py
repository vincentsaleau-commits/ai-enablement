from datetime import datetime, timezone

import pytest

from support_triage.analysis import queue_snapshot, search_tickets


def test_queue_snapshot_calculates_age_and_reply_sla():
    tickets = [
        {
            "id": "T-1",
            "status": "open",
            "subject": "Withdrawal pending",
            "body": "",
            "created_at": "2026-10-29T08:00:00Z",
            "first_reply_at": "2026-10-29T08:30:00Z",
        },
        {
            "id": "T-2",
            "status": "new",
            "subject": "Bonus question",
            "body": "",
            "created_at": "2026-10-29T09:30:00Z",
            "first_reply_at": "2026-10-29T11:00:00Z",
        },
        {
            "id": "T-3",
            "status": "solved",
            "subject": "Old deposit question",
            "body": "",
            "created_at": "2026-10-29T06:00:00Z",
            "first_reply_at": "2026-10-29T06:15:00Z",
        },
    ]
    fixed_now = datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc)

    snapshot = queue_snapshot(tickets, fixed_now)

    assert snapshot["open_ticket_count"] == 2
    assert snapshot["queue_age_median_hours"] == 1.25
    assert snapshot["oldest_open_ticket"] == {"age_hours": 2.0}
    assert snapshot["first_reply_sample_count"] == 2
    assert snapshot["first_reply_sla_under_one_hour_pct"] == 100.0
    assert snapshot["topic_indicators"] == {"withdrawal": 1, "bonus": 1}


def test_search_returns_aggregate_counts_without_ticket_content():
    tickets = [
        {
            "id": "T-1",
            "status": "open",
            "subject": "Withdrawal help",
            "body": "Contact jane@example.com or +1 415 555 0199",
        },
        {"id": "T-2", "status": "closed", "subject": "Withdrawal resolved", "body": ""},
    ]

    results = search_tickets(tickets, "withdrawal")

    assert results == {
        "matched_ticket_count": 1,
        "topic_indicators": {"withdrawal": 1},
    }
    assert "T-1" not in str(results)
    assert "jane@example.com" not in str(results)
    assert "Withdrawal help" not in str(results)


@pytest.mark.parametrize("query,limit", [("", 10), ("withdrawal", 0), ("withdrawal", 51)])
def test_search_rejects_empty_query_and_unbounded_limits(query, limit):
    with pytest.raises(ValueError):
        search_tickets([], query, limit)