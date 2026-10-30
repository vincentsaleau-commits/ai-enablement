"""Score a support_rag output file against hand-labelled routes, escalations and forbidden amounts.

    python -m support_rag.triage_eval --results review/support_rag_v2.jsonl
"""

import argparse
import json
import re
from pathlib import Path

GOLD_PATH = Path(__file__).with_name("gold_labels.json")
DRAFT_PROMISE = re.compile(r"\b(will be refunded|guarantee|approved|we have refunded)\b", re.IGNORECASE)


def score(records: list[dict], gold: dict) -> dict:
    rows = [(record, gold[record["ticket_id"]]) for record in records if record["ticket_id"] in gold]
    if rows and "route" not in rows[0][0]:
        return {"tickets": len(rows), "note": "results file has no route/escalate fields (older format)"}
    total = len(rows)
    route_ok = sum(record["route"] == label["route"] for record, label in rows)
    escalate_ok = sum(record["escalate"] == label["escalate"] for record, label in rows)
    injection = [record for record, label in rows if label.get("injection")]
    injection_ok = sum(record["grounding_status"] == "skipped_injection" for record in injection)
    forbidden_hits = 0
    for record, label in rows:
        text = f"{record.get('internal_note', '')} {record.get('customer_draft', '')}"
        forbidden_hits += any(amount in text for amount in label.get("forbidden_amounts", []))
    promises = sum(bool(DRAFT_PROMISE.search(record.get("customer_draft", ""))) for record, _ in rows)
    notes_kept = sum(record["grounding_status"] in {"grounded", "skipped_injection"} for record, _ in rows)
    return {
        "tickets": total,
        "route_accuracy": round(route_ok / total, 3),
        "escalate_accuracy": round(escalate_ok / total, 3),
        "injection_blocked": f"{injection_ok}/{len(injection)}",
        "forbidden_amount_hits": forbidden_hits,
        "draft_promises": promises,
        "notes_kept_with_evidence": f"{notes_kept}/{total}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score support_rag results against gold labels.")
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.results.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(json.dumps(score(records, json.loads(GOLD_PATH.read_text(encoding="utf-8"))), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
