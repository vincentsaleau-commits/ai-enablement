import re
from collections import Counter
from datetime import datetime, timezone
from statistics import median
from typing import Any

from support_triage.data import is_open


TOPIC_KEYWORDS = {
    "withdrawal": ("withdraw", "cashout", "cash out", "payout"),
    "bonus": ("bonus", "promotion", "promo", "wagering", "rollover"),
    "deposit": ("deposit", "top up", "top-up", "payment"),
    "account_access": ("login", "password", "locked", "verification", "kyc"),
}
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
LONG_NUMBER_PATTERN = re.compile(r"(?<!\w)\d{7,}(?!\w)")


def classify_topic(ticket: dict[str, str]) -> str:
    text = f"{ticket.get('subject', '')} {ticket.get('body', '')}".lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return topic
    return "other"


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _hours_between(start: str, end: datetime) -> float | None:
    parsed = _parse_timestamp(start)
    if parsed is None:
        return None
    return max(0.0, (end - parsed).total_seconds() / 3600)


def redact_text(value: str) -> str:
    redacted = EMAIL_PATTERN.sub("[email redacted]", value)
    redacted = PHONE_PATTERN.sub("[phone redacted]", redacted)
    return LONG_NUMBER_PATTERN.sub("[number redacted]", redacted)


def queue_snapshot(
    tickets: list[dict[str, str]], now: datetime | None = None
) -> dict[str, Any]:
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    open_tickets = [ticket for ticket in tickets if is_open(ticket)]
    queue_ages = [
        age
        for ticket in open_tickets
        if (age := _hours_between(ticket.get("created_at", ""), current_time)) is not None
    ]
    first_reply_times = [
        (reply - created).total_seconds() / 3600
        for ticket in tickets
        if (created := _parse_timestamp(ticket.get("created_at", ""))) is not None
        and (reply := _parse_timestamp(ticket.get("first_reply_at", ""))) is not None
        and created <= reply <= current_time
    ]
    statuses = Counter(ticket["status"].strip().lower() for ticket in open_tickets)
    topics = Counter(classify_topic(ticket) for ticket in open_tickets)
    oldest_ticket = None
    if queue_ages:
        oldest_ticket = max(
            (
                (ticket, _hours_between(ticket.get("created_at", ""), current_time))
                for ticket in open_tickets
            ),
            key=lambda item: item[1] if item[1] is not None else -1,
        )

    return {
        "open_ticket_count": len(open_tickets),
        "by_status": dict(statuses),
        "topic_indicators": dict(topics),
        "queue_age_median_hours": round(median(queue_ages), 2) if queue_ages else None,
        "oldest_open_ticket": (
            {"age_hours": round(oldest_ticket[1], 2)}
            if oldest_ticket and oldest_ticket[1] is not None
            else None
        ),
        "first_reply_sample_count": len(first_reply_times),
        "first_reply_median_hours": (
            round(median(first_reply_times), 2) if first_reply_times else None
        ),
        "first_reply_sla_under_one_hour_pct": (
            round(sum(hours <= 1 for hours in first_reply_times) * 100 / len(first_reply_times), 1)
            if first_reply_times
            else None
        ),
        "classification_note": "Topic counts are keyword indicators, not verified root causes.",
    }


def search_tickets(
    tickets: list[dict[str, str]], query: str, limit: int = 50
) -> dict[str, Any]:
    """Return aggregate counts only. Ticket IDs, subjects, and message text are never returned.

    `limit` caps how many matching open tickets are counted.
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    needle = query.casefold()
    matched: list[dict[str, str]] = []
    for ticket in tickets:
        if not is_open(ticket):
            continue
        searchable_text = f"{ticket.get('subject', '')} {ticket.get('body', '')}"
        if needle in searchable_text.casefold():
            matched.append(ticket)
            if len(matched) >= limit:
                break
    topics = Counter(classify_topic(ticket) for ticket in matched)
    return {
        "matched_ticket_count": len(matched),
        "topic_indicators": dict(topics),
    }