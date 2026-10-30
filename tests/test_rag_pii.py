import csv
import json

from support_rag.engine import run_batch
from support_rag.pii import load_case_context, mask_pii


class CapturingOllama:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.embedded_texts: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append(
                [
                    float("withdraw" in lowered or "pending" in lowered),
                    float("bonus" in lowered),
                    float("quickpay" in lowered),
                ]
            )
        return vectors

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(
            {
                "category": "withdrawal",
                "recommended_action": "Check the pending status.",
                "draft_reply": "We are checking your request.",
                "citations": ["E1"],
                "abstain": False,
            }
        )

    def verify_grounding(self, question, suggestion, evidence) -> bool:
        return True


def write_csv(path, headers: list[str], row: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerow(row)


def test_case_context_masks_identifiers_and_allowlists_sensitive_csv_fields(tmp_path) -> None:
    write_csv(
        tmp_path / "customers.csv",
        [
            "customer_id", "full_name", "email", "phone", "country", "currency",
            "vip_tier", "kyc_status", "kyc_review_reason", "self_excluded", "balance",
            "registered_at",
        ],
        [
            "C-TEST-1", "Avery Example", "avery@example.test", "+1-202-555-0188",
            "Atlantis", "USD", "gold", "pending", "PRIVATE-KYC-REASON", "false",
            "2468.00", "2026-01-01",
        ],
    )
    write_csv(
        tmp_path / "transactions.csv",
        [
            "txn_id", "customer_id", "type", "amount", "currency", "status",
            "provider", "created_at", "updated_at", "note",
        ],
        [
            "TX-TEST-9", "C-TEST-1", "withdrawal", "1234.56", "USD", "pending",
            "QuickPay", "2026-09-20T10:00:00Z", "2026-09-21T10:00:00Z", "PRIVATE-TXN-NOTE",
        ],
    )

    context = load_case_context({"customer_id": "C-TEST-1"}, tmp_path)
    safe_context = "\n".join(text for _, text in context.chunks)

    assert "kyc_status=pending" in safe_context
    assert "self_excluded=false" in safe_context
    assert "type=withdrawal" in safe_context
    assert "status=pending" in safe_context
    assert "provider=QuickPay" in safe_context
    for secret in (
        "Avery Example", "avery@example.test", "+1-202-555-0188", "Atlantis",
        "C-TEST-1", "TX-TEST-9", "2468.00", "1234.56", "PRIVATE-KYC-REASON",
        "PRIVATE-TXN-NOTE",
    ):
        assert secret not in safe_context
        assert secret in context.pii_values


def test_mask_pii_redacts_known_values_emails_phones_ids_and_amounts() -> None:
    text = "Avery Example avery@example.test +1-202-555-0188 C-TEST-1 TX-TEST-9 $1,234.56"

    masked = mask_pii(text, ("Avery Example", "C-TEST-1", "TX-TEST-9"))

    assert "Avery Example" not in masked
    assert "avery@example.test" not in masked
    assert "+1-202-555-0188" not in masked
    assert "C-TEST-1" not in masked
    assert "TX-TEST-9" not in masked
    assert "$1,234.56" not in masked


def test_run_batch_masks_ticket_and_csv_pii_before_embedding_and_generation(tmp_path) -> None:
    export_path = tmp_path / "tickets.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "ticket_id": "T-TEST-1",
                    "customer_id": "C-TEST-1",
                    "status": "open",
                    "subject": "Withdrawal for Avery Example",
                    "message": "Contact avery@example.test at +1-202-555-0188 about $1,234.56 (TX-TEST-9).",
                }
            ]
        ),
        encoding="utf-8",
    )
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "support-handbook-v2.md").write_text("Withdrawal approvals take 24 hours.", encoding="utf-8")
    (knowledge_dir / "bonus-terms.md").write_text("Bonus terms vary by game.", encoding="utf-8")
    write_csv(
        knowledge_dir / "customers.csv",
        ["customer_id", "full_name", "email", "phone", "country", "currency", "vip_tier", "kyc_status", "kyc_review_reason", "self_excluded", "balance", "registered_at"],
        ["C-TEST-1", "Avery Example", "avery@example.test", "+1-202-555-0188", "Atlantis", "USD", "gold", "pending", "PRIVATE-KYC-REASON", "false", "2468.00", "2026-01-01"],
    )
    write_csv(
        knowledge_dir / "transactions.csv",
        ["txn_id", "customer_id", "type", "amount", "currency", "status", "provider", "created_at", "updated_at", "note"],
        ["TX-TEST-9", "C-TEST-1", "withdrawal", "1234.56", "USD", "pending", "QuickPay", "2026-09-20T10:00:00Z", "2026-09-21T10:00:00Z", "PRIVATE-TXN-NOTE"],
    )
    ollama = CapturingOllama()

    run_batch(export_path, knowledge_dir, tmp_path / "review.jsonl", ollama)

    prompt = ollama.prompts[0]
    embedded_text = "\n".join(ollama.embedded_texts)
    for secret in (
        "Avery Example", "avery@example.test", "+1-202-555-0188", "C-TEST-1",
        "TX-TEST-9", "$1,234.56", "PRIVATE-KYC-REASON", "PRIVATE-TXN-NOTE", "2468.00",
    ):
        assert secret not in prompt
        assert secret not in embedded_text
    assert "kyc_status=pending" in prompt
    assert "provider=QuickPay" in prompt