import json

from support_triage.data import load_tickets


def test_loads_csv_and_returns_only_open_tickets(tmp_path):
    export_path = tmp_path / "tickets.csv"
    export_path.write_text(
        "id,status,subject,created_at\n"
        "T-1,open,Withdrawal pending,2026-10-28T10:00:00Z\n"
        "T-2,closed,Bonus question,2026-10-28T11:00:00Z\n",
        encoding="utf-8",
    )

    tickets = load_tickets(export_path)

    assert [ticket["id"] for ticket in tickets] == ["T-1"]
    assert tickets[0]["subject"] == "Withdrawal pending"


def test_loads_json_export_with_ticket_collection(tmp_path):
    export_path = tmp_path / "tickets.json"
    export_path.write_text(
        json.dumps(
            {
                "tickets": [
                    {"id": 7, "status": "new", "subject": "Deposit question"},
                    {"id": 8, "status": "solved", "subject": "Resolved"},
                ]
            }
        ),
        encoding="utf-8",
    )

    tickets = load_tickets(export_path)

    assert [ticket["id"] for ticket in tickets] == ["7"]


def test_rejects_export_without_required_ticket_fields(tmp_path):
    export_path = tmp_path / "invalid.csv"
    export_path.write_text("subject\nMissing columns\n", encoding="utf-8")

    try:
        load_tickets(export_path)
    except ValueError as error:
        assert "status" in str(error)
    else:
        raise AssertionError("Expected invalid export to be rejected")