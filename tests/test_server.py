import json

import pytest
from mcp import Client

from support_triage.server import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_snapshot_reads_local_export(tmp_path, monkeypatch):
    export_path = tmp_path / "tickets.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "id": "T-1",
                    "status": "open",
                    "subject": "Withdrawal pending",
                    "created_at": "2026-10-28T10:00:00Z",
                },
                {"id": "T-2", "status": "solved", "subject": "Bonus resolved"},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SUPPORT_EXPORT_PATH", str(export_path))

    async with Client(mcp) as client:
        result = await client.call_tool("support_queue_snapshot", {})

    assert not result.is_error, result.content
    assert result.structured_content["open_ticket_count"] == 1
    assert result.structured_content["topic_indicators"] == {"withdrawal": 1}


@pytest.mark.anyio
async def test_mcp_review_tool_marks_submission_unverified(tmp_path, monkeypatch):
    export_path = tmp_path / "tickets.csv"
    export_path.write_text("id,status,subject\nT-1,open,Bonus question\n", encoding="utf-8")
    log_path = tmp_path / "review.jsonl"
    monkeypatch.setenv("SUPPORT_EXPORT_PATH", str(export_path))
    monkeypatch.setenv("SUPPORT_REVIEW_LOG_PATH", str(log_path))

    async with Client(mcp) as client:
        result = await client.call_tool(
            "record_triage_decision",
            {
                "ticket_id": "T-1",
                "category": "bonus",
                "disposition": "needs_policy_review",
                "rationale": "Verify against the current bonus policy.",
                "reviewer": "Mai",
            },
        )

    assert not result.is_error
    assert result.structured_content == {
        "recorded": "true",
        "review_status": "unverified",
    }
    assert '"review_status": "unverified"' in log_path.read_text(encoding="utf-8")