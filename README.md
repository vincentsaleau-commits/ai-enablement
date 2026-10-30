# Support RAG

A local tool for the support queue. It reads tickets from the export, decides escalation and routing with fixed rules, and asks a local model to write an internal note for a reviewer. It never contacts customers, issues refunds, or changes accounts.

## Run

Requirements: Python 3.11+, Ollama on `127.0.0.1` with `nomic-embed-text` and `qwen2.5:3b`, and the export in `bf66c640cc851ef616bfad90e4822573/`.

0. Clone the export into the project folder (one time). It is a separate git repo, so it is not part of this one:

   ```bash
   git clone https://gist.github.com/bf66c640cc851ef616bfad90e4822573.git bf66c640cc851ef616bfad90e4822573
   ```

1. Install the Ollama models once, with Ollama running:

   ```bash
   ollama pull nomic-embed-text
   ollama pull qwen2.5:3b
   ollama list   # both models should appear
   ```

2. Set up the Python environment:

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate
   python -m pip install -e ".[dev]"
   ```

3. Run the batch on the open tickets:

```bash
OLLAMA_GENERATION_MODEL=qwen2.5:3b OLLAMA_EMBEDDING_MODEL=nomic-embed-text \
python -m support_rag.cli \
  --export bf66c640cc851ef616bfad90e4822573/tickets.json \
  --knowledge-dir bf66c640cc851ef616bfad90e4822573 \
  --output review/support_rag_r1_open.jsonl
```

The output is a JSONL file with one record per open ticket. The `review/` folder is created if it does not exist. Each record is `review_status: unverified` and `requires_human_review: true`. `review/` is listed in `.gitignore`, so these files stay on this machine and are not committed.

## How a ticket is handled

1. **Rules decide** (`support_rag/rules.py`), from the raw ticket text and `customers.csv`: injected instructions, gambling harm, self-exclusion, legal or chargeback threats, suspected fraud, another person's account, account reopening, refunds above $100 or with no amount, account access, bonus withdrawals, and pending or missing withdrawals (routed to Payments).
2. **Policy is limited per ticket.** Only the handbook sections the rules allow are retrieved. Escalated tickets read the escalation section.
3. **The model writes a note** from those sections only. It is not allowed to decide eligibility, refunds, or exceptions. Injected tickets skip the model.
4. **Checks** drop a note that has numbers, timelines, or decision phrases not found in the sources, copies the customer's message, or reads like a letter. A dropped note is replaced with a fixed message.
5. **KYC status** from `customers.csv` is returned on every record. A non-verified status is also added to the note. The KYC review reason is for the reviewer only and never goes into a customer draft.
6. **Customer drafts** come from fixed templates and never promise an outcome. Escalated tickets get only an acknowledgement.
7. Every record is `review_status: unverified` and `requires_human_review: true`. A person checks, edits, and sends.

## Results (30 sample tickets, 3 runs)

- Routes are identical across runs.
- Note status is stable for 26 of 30 tickets. Three tickets had an error in at least one run (T-5005, T-5106, T-5110). The results are in the comparison table in `ANSWERS.md`.

## Data handling

- Policy sources: `support-handbook-v2.md` and `bonus-terms.md` only. Handbook v1, Slack, marketing, and finance files are not used.
- Customer and transaction data are used as case context, with personal data masked before any text reaches the model.
- Output stays on this machine. The model runs locally through Ollama.

## Tests

```bash
python -m pytest tests -q
```

The tests cover the rules, the note checks, KYC and self-exclusion handling, retrieval limits, and the evaluation scorer. They use mocked Ollama calls and verify execution, not policy accuracy.

## Limits

- Rules are English-first. Vietnamese keywords cover deposit, withdrawal, and bonus only. Other languages escalate by default.
- Templates are in English. Drafts in other languages need a person to rewrite them.
- "Pending" and "not arrived" are the withdrawal delay signal. The tool does not know the actual status; Payments does.
- Thresholds ($100, 24 hours, 3 business days) are copied from handbook v2, not computed from timestamps.
- The handbook has no threshold for KYC checks on large withdrawals, so that case is not automated.
- The model can still write a grounded-looking note that is wrong. The checks catch numbers, timelines, and decision phrases, not every wrong topic.

## Judgement

I would not let a model decide refunds or eligibility from ticket text. The export contains a ticket that tries to override the assistant, and a model would have to be trusted to ignore it. Rules a person can read are the better trade here.
