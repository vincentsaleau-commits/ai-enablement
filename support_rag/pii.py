import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CUSTOMER_PII_FIELDS = (
    "customer_id",
    "full_name",
    "email",
    "phone",
    "country",
    "balance",
    "kyc_review_reason",
)
TRANSACTION_PRIVATE_FIELDS = ("txn_id", "customer_id", "amount", "note")
CUSTOMER_CONTEXT_FIELDS = ("kyc_status", "self_excluded")
TRANSACTION_CONTEXT_FIELDS = ("type", "status", "provider", "created_at", "updated_at")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+\d{1,3}[ .()-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\w)")
AMOUNT_PATTERN = re.compile(
    r"(?i)(?:[$€£]\s*\d[\d,]*(?:\.\d{1,2})?|\b\d[\d.,]*\s*(?:USD|EUR|GBP|VND|VNĐ|đồng|dong|đ)\b)"
)
IDENTIFIER_PATTERN = re.compile(r"(?i)\b(?:C|TX|T)-\d+\b")


@dataclass(frozen=True)
class MaskedCaseContext:
    chunks: tuple[tuple[str, str], ...]
    pii_values: tuple[str, ...]


def load_case_context(ticket: dict[str, str], knowledge_dir: str | Path) -> MaskedCaseContext:
    directory = Path(knowledge_dir).expanduser()
    customer_id = ticket.get("customer_id", "").strip()
    pii_values: set[str] = {customer_id} if customer_id else set()
    chunks: list[tuple[str, str]] = []

    customer_path = directory / "customers.csv"
    if customer_path.is_file():
        customer_rows = _read_csv(customer_path)
        for row in customer_rows:
            pii_values.update(_nonempty_values(row, CUSTOMER_PII_FIELDS))
        customer = next(
            (row for row in customer_rows if customer_id and row.get("customer_id", "").strip() == customer_id),
            None,
        )
        if customer:
            facts = _format_facts(customer, CUSTOMER_CONTEXT_FIELDS)
            if facts:
                chunks.append(("customers.csv", "Customer operational context: " + facts))

    transaction_path = directory / "transactions.csv"
    if transaction_path.is_file():
        transaction_rows = _read_csv(transaction_path)
        for row in transaction_rows:
            pii_values.update(_nonempty_values(row, TRANSACTION_PRIVATE_FIELDS))
        matching_transactions = [
            row
            for row in transaction_rows
            if customer_id and row.get("customer_id", "").strip() == customer_id
        ]
        for row in matching_transactions[-5:]:
            facts = _format_facts(row, TRANSACTION_CONTEXT_FIELDS)
            if facts:
                chunks.append(("transactions.csv", "Transaction operational context: " + facts))

    return MaskedCaseContext(
        chunks=tuple(chunks),
        pii_values=tuple(sorted((value for value in pii_values if len(value) >= 3), key=len, reverse=True)),
    )


def mask_pii(text: str, known_values: Iterable[str] = ()) -> str:
    masked = text
    for value in sorted((value for value in known_values if value.strip()), key=len, reverse=True):
        masked = re.sub(
            rf"(?<!\w){re.escape(value.strip())}(?!\w)",
            "[REDACTED]",
            masked,
            flags=re.IGNORECASE,
        )
    masked = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", masked)
    masked = PHONE_PATTERN.sub("[REDACTED_PHONE]", masked)
    masked = AMOUNT_PATTERN.sub("[REDACTED_AMOUNT]", masked)
    return IDENTIFIER_PATTERN.sub("[REDACTED_ID]", masked)


def load_kyc(customer_id: str, knowledge_dir: str | Path) -> tuple[str, str]:
    """Return (kyc_status, kyc_review_reason) for a customer. Unknown customers are reported as 'unknown'."""
    path = Path(knowledge_dir).expanduser() / "customers.csv"
    if not customer_id or not path.is_file():
        return "unknown", ""
    for row in _read_csv(path):
        if row.get("customer_id", "") == customer_id:
            return row.get("kyc_status", "") or "unknown", row.get("kyc_review_reason", "")
    return "unknown", ""


def load_self_excluded(customer_id: str, knowledge_dir: str | Path) -> bool:
    """True when customers.csv marks the customer as self-excluded from gambling."""
    path = Path(knowledge_dir).expanduser() / "customers.csv"
    if not customer_id or not path.is_file():
        return False
    for row in _read_csv(path):
        if row.get("customer_id", "") == customer_id:
            return row.get("self_excluded", "").lower() == "true"
    return False


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return [
            {key.strip().lower(): (value or "").strip() for key, value in row.items() if key}
            for row in csv.DictReader(csv_file)
        ]


def _nonempty_values(row: dict[str, str], fields: tuple[str, ...]) -> set[str]:
    return {row[field] for field in fields if row.get(field)}


def _format_facts(row: dict[str, str], fields: tuple[str, ...]) -> str:
    return "; ".join(f"{field}={row[field]}" for field in fields if row.get(field))