import json
import sys
from datetime import datetime, timezone

from support_triage.analysis import queue_snapshot
from support_triage.report import build_report, main


def test_report_masks_contact_details_in_subjects():
    tickets = [
        {
            "id": "T-1",
            "status": "open",
            "subject": "Help for jane@example.com",
            "body": "",
        }
    ]

    report = build_report(tickets, queue_snapshot(tickets))

    assert "jane@example.com" not in report
    assert "[email redacted]" in report


def test_first_reply_sample_includes_closed_tickets():
    tickets = [
        {
            "id": "T-1",
            "status": "closed",
            "subject": "withdrawal",
            "created_at": "2026-09-01T10:00:00Z",
            "first_reply_at": "2026-09-01T10:30:00Z",
        },
        {
            "id": "T-2",
            "status": "open",
            "subject": "withdrawal",
            "created_at": "2026-09-01T10:00:00Z",
            "first_reply_at": "",
        },
    ]

    snapshot = queue_snapshot(tickets, now=datetime(2026, 9, 2, tzinfo=timezone.utc))

    assert snapshot["first_reply_sample_count"] == 1
    assert snapshot["first_reply_median_hours"] == 0.5


def test_queue_age_uses_as_of_time_and_report_states_it():
    tickets = [
        {
            "id": "T-1",
            "status": "open",
            "subject": "withdrawal",
            "created_at": "2026-09-29T00:00:00Z",
            "first_reply_at": "",
        }
    ]
    as_of = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)

    snapshot = queue_snapshot(tickets, now=as_of)
    report = build_report(tickets, snapshot, measured_at=as_of)

    assert snapshot["queue_age_median_hours"] == 9.0
    assert "Measured as of: 2026-09-29T09:00:00+00:00" in report


def test_cli_writes_open_ticket_report_from_synthetic_export(tmp_path, monkeypatch):
    export = tmp_path / "tickets.json"
    export.write_text(
        json.dumps(
            [
                {
                    "ticket_id": "T-1",
                    "status": "closed",
                    "subject": "withdrawal",
                    "created_at": "2026-09-28T10:00:00Z",
                    "first_response_at": "2026-09-28T10:30:00Z",
                },
                {
                    "ticket_id": "T-2",
                    "status": "open",
                    "subject": "Bonus for bob@example.com",
                    "created_at": "2026-09-29T00:00:00Z",
                    "first_response_at": None,
                },
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "report.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report",
            "--export",
            str(export),
            "--output",
            str(output),
            "--as-of",
            "2026-09-29T09:00:00",
        ],
    )

    main()

    text = output.read_text(encoding="utf-8")
    assert "Measured as of: 2026-09-29T09:00:00+00:00" in text
    assert "Open tickets: 1" in text
    assert "Median current queue age (hours): 9.0" in text
    assert "measurement): 1" in text
    assert "- T-2: Bonus for [email redacted] (open)" in text
    assert "T-1" not in text.split("## Open Ticket IDs")[1]