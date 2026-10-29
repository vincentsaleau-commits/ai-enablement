import csv
import json
from pathlib import Path
from typing import Any


FIELD_ALIASES = {
    "id": ("id", "ticket_id", "ticket id", "case_id"),
    "status": ("status", "state"),
    "subject": ("subject", "title", "summary"),
    "body": ("body", "description", "message", "content", "latest_message"),
    "created_at": ("created_at", "created", "date_created", "created date"),
    "first_reply_at": (
        "first_reply_at",
        "first_reply",
        "first response at",
        "first_response_at",
    ),
    "priority": ("priority", "urgency"),
    "tags": ("tags", "labels", "category"),
}
TERMINAL_STATUSES = {"closed", "solved", "resolved", "deleted", "archived", "complete"}


def _normalize_header(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_")


def _rows_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict):
        rows = next(
            (value[key] for key in ("tickets", "data", "results", "rows") if key in value),
            None,
        )
        if rows is None:
            raise ValueError("JSON export must be a list or contain tickets/data/results/rows")
    else:
        raise ValueError("JSON export must contain a list of ticket objects")

    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Ticket collection must contain JSON objects")
    return rows


def _canonicalize(row: dict[str, Any]) -> dict[str, str]:
    normalized = {_normalize_header(key): value for key, value in row.items()}
    ticket: dict[str, str] = {}
    for field, aliases in FIELD_ALIASES.items():
        value = next((normalized[name] for name in aliases if name in normalized), "")
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        ticket[field] = str(value).strip() if value is not None else ""
    return ticket


def is_open(ticket: dict[str, str]) -> bool:
    status = ticket.get("status", "").strip().lower().replace(" ", "_")
    return bool(status) and status not in TERMINAL_STATUSES


def load_tickets(path: str | Path, open_only: bool = True) -> list[dict[str, str]]:
    """Load a CSV or JSON ticket export and normalize common field names."""
    export_path = Path(path).expanduser()
    if not export_path.is_file():
        raise FileNotFoundError(f"Ticket export not found: {export_path}")

    try:
        if export_path.suffix.lower() == ".csv":
            with export_path.open(encoding="utf-8-sig", newline="") as export_file:
                reader = csv.DictReader(export_file)
                rows = list(reader)
                headers = {_normalize_header(name) for name in (reader.fieldnames or [])}
        elif export_path.suffix.lower() == ".json":
            with export_path.open(encoding="utf-8-sig") as export_file:
                rows = _rows_from_json(json.load(export_file))
            headers = {_normalize_header(key) for row in rows for key in row}
        else:
            raise ValueError("Unsupported export format; use .csv or .json")
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON export: {export_path}") from error

    missing_fields = [
        field
        for field in ("id", "status", "subject")
        if not headers.intersection(FIELD_ALIASES[field])
    ]
    if missing_fields:
        raise ValueError(f"Export is missing required fields: {', '.join(missing_fields)}")

    tickets = [_canonicalize(row) for row in rows]
    if any(not ticket["id"] for ticket in tickets):
        raise ValueError("Every ticket must have a non-empty ID")
    return [ticket for ticket in tickets if not open_only or is_open(ticket)]