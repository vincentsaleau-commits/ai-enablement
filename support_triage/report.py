import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from support_triage.analysis import queue_snapshot, redact_text
from support_triage.data import is_open, load_tickets


def build_report(
    tickets: list[dict[str, str]],
    snapshot: dict[str, Any],
    measured_at: datetime | None = None,
) -> str:
    measured_label = (
        measured_at.astimezone(timezone.utc).isoformat()
        if measured_at
        else "run time (no --as-of given; not an export timestamp)"
    )
    lines = [
        "# Open Support Ticket Snapshot",
        "",
        "> Topic labels are keyword indicators, not verified root causes or policy decisions.",
        "",
        f"- Measured as of: {measured_label}",
        f"- Open tickets: {snapshot['open_ticket_count']}",
        f"- Median current queue age (hours): {snapshot['queue_age_median_hours']}",
        f"- First-reply sample count (all tickets with a reply at or before measurement): "
        f"{snapshot['first_reply_sample_count']}",
        f"- Median first reply (hours): {snapshot['first_reply_median_hours']}",
        f"- First replies within 1 hour: {snapshot['first_reply_sla_under_one_hour_pct']}%",
        "- Oldest open ticket age (hours): "
        f"{snapshot['oldest_open_ticket']['age_hours'] if snapshot['oldest_open_ticket'] else 'none'}",
        "",
        "## Topic Indicators",
        "",
    ]
    lines.extend(
        f"- {topic}: {count}" for topic, count in sorted(snapshot["topic_indicators"].items())
    )
    lines.extend(["", "## Open Ticket IDs", ""])
    lines.extend(
        f"- {ticket['id']}: {redact_text(ticket['subject'])} ({ticket['status']})"
        for ticket in tickets
    )
    lines.append("")
    return "\n".join(lines)


def _parse_as_of(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Report on unresolved support tickets.")
    parser.add_argument("--export", required=True, help="Path to a local CSV or JSON export")
    parser.add_argument("--output", help="Optional path to save the Markdown report")
    parser.add_argument(
        "--as-of",
        type=_parse_as_of,
        default=None,
        help="ISO timestamp to measure queue age and replies at (naive values are UTC). "
        "Use the export's own timestamp so ages are not inflated by the run date.",
    )
    args = parser.parse_args()

    # Load every ticket: first-reply metrics need closed tickets too.
    all_tickets = load_tickets(args.export, open_only=False)
    open_tickets = [ticket for ticket in all_tickets if is_open(ticket)]
    snapshot = queue_snapshot(all_tickets, now=args.as_of)
    report = build_report(open_tickets, snapshot, measured_at=args.as_of)
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()