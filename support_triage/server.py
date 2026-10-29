import logging
import os
from pathlib import Path
from typing import Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from support_triage.analysis import queue_snapshot, search_tickets
from support_triage.data import load_tickets
from support_triage.reviews import record_review


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
mcp = MCPServer("support-ticket-triage")


def _export_path() -> Path:
    value = os.environ.get("SUPPORT_EXPORT_PATH")
    if not value:
        raise ValueError("Set SUPPORT_EXPORT_PATH to a local CSV or JSON export")
    return Path(value).expanduser()


@mcp.tool()
def support_queue_snapshot() -> dict[str, Any]:
    """Summarize unresolved tickets, queue age, first replies, and topic indicators."""
    tickets = load_tickets(_export_path(), open_only=False)
    return queue_snapshot(tickets)


@mcp.tool()
def search_support_tickets(query: str) -> dict[str, Any]:
    """Count open tickets matching a keyword, with topic indicators only. No ticket IDs or text are returned."""
    tickets = load_tickets(_export_path())
    return search_tickets(tickets, query)


@mcp.tool()
def record_triage_decision(
    ticket_id: str,
    category: Literal["withdrawal", "bonus", "deposit", "account_access", "other"],
    disposition: Literal[
        "needs_policy_review", "process_issue", "policy_confirmed", "not_relevant"
    ],
    rationale: str,
    reviewer: str,
) -> dict[str, str]:
    """Append a caller-submitted triage note to a local JSONL log. It is marked unverified and never changes the export."""
    export_path = _export_path()
    log_path = Path(
        os.environ.get(
            "SUPPORT_REVIEW_LOG_PATH",
            str(Path(__file__).resolve().parents[1] / "review" / "decisions.jsonl"),
        )
    )
    try:
        result = record_review(
            export_path=export_path,
            log_path=log_path,
            ticket_id=ticket_id,
            category=category,
            disposition=disposition,
            rationale=rationale,
            reviewer=reviewer,
        )
    except ValueError as error:
        raise ToolError(str(error)) from error
    logger.info("Recorded unverified triage note for ticket %s", ticket_id)
    return {"recorded": "true", "review_status": result["review_status"]}


if __name__ == "__main__":
    mcp.run(transport="stdio")