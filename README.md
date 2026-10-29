# Support Ticket Triage

A local-first support operations tool for the 99Tech AI Enablement challenge. It reads a CSV or JSON export, measures the open queue and first-reply SLA where timestamps exist, surfaces keyword-based topic indicators, searches open tickets with common contact details masked, and appends caller-submitted, unverified triage decisions to a separate JSONL audit log.

It does not draft or send customer replies, decide bonus or withdrawal eligibility, issue refunds, or modify the source export. The first proposed fix is operational visibility and a caller-submitted, unverified policy/process classification. The supplied export contains two handbook versions and bonus terms, but the tool does not read them; automating eligibility decisions from them would be unsafe and premature.

## Requirements

- Python 3.11 or newer on `PATH`
- Claude Desktop for the MCP workflow

## Install and run

From the project directory in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Put the support export in a local, access-controlled folder. Supported input is `.csv` or `.json`. CSV needs ID, status, and subject columns; JSON must be a list of ticket objects or an object containing a `tickets`, `data`, `results`, or `rows` list. Common aliases are normalized in [support_triage/data.py](support_triage/data.py). Created/first-reply timestamps are optional; without them the corresponding timing metric is reported as unavailable. The raw export remains where it is.

Generate a Markdown report from all open tickets:

```powershell
python -m support_triage.report --export "D:\data\support-export.csv" --output "artifacts\open_tickets_report.md"
```

Pass `--as-of` with the export's own timestamp so queue ages and replies are measured at the export time rather than the run time. Naive timestamps are read as UTC. The report header states the measurement time.

```powershell
python -m support_triage.report --export "bf66c640cc851ef616bfad90e4822573\tickets.json" --as-of "2026-09-29T09:00:00Z" --output "artifacts\open_tickets_report.md"
```

All tickets are loaded so that the first-reply sample includes closed tickets. Only open tickets are listed.

Run the MCP server directly:

```powershell
$env:SUPPORT_EXPORT_PATH = "D:\data\support-export.csv"
$env:SUPPORT_REVIEW_LOG_PATH = "D:\data\triage-decisions.jsonl"
python -m support_triage.server
```

The MCP tools are:

- `support_queue_snapshot`: open queue size/status, median queue age, oldest open ticket age (no ID), first-reply median and one-hour SLA rate using only replies at or before the measurement time, plus keyword topic indicators.
- `search_support_tickets`: returns aggregate counts (matched ticket count and topic indicators) only. No ticket IDs, subjects, or message text are returned to the MCP client.
- `record_triage_decision`: append a caller-submitted category/disposition, rationale, reviewer name, and timestamp to a JSONL file separate from the export. Records are marked `review_status: unverified`.

## Claude Desktop (Windows)

Merge this entry into `%APPDATA%\Claude\claude_desktop_config.json`, replacing the paths with absolute paths on your machine. Preserve any existing `mcpServers` entries. The environment values are local paths; don't commit real exports or review logs.

```json
{
  "mcpServers": {
    "support-ticket-triage": {
      "command": "D:\\Projects\\personal\\AI Enablement\\.venv\\Scripts\\python.exe",
      "args": ["-m", "support_triage.server"],
      "cwd": "D:\\Projects\\personal\\AI Enablement",
      "env": {
        "SUPPORT_EXPORT_PATH": "D:\\data\\support-export.csv",
        "SUPPORT_REVIEW_LOG_PATH": "D:\\data\\triage-decisions.jsonl"
      }
    }
  }
}
```

Fully quit and restart Claude Desktop after editing the config. The MCP server uses stdio; it writes logs to stderr, not stdout.

## Safety and data handling

- No network calls, database, or live support-system credentials are used.
- MCP tool outputs contain aggregates only, so ticket text and IDs do not reach the MCP client. Full ticket detail stays in the locally generated Markdown report.
- The Markdown report also masks common contact details in ticket subjects. Ticket IDs remain present to support reconciliation; store generated reports as sensitive data.
- Queue metrics are derived from supplied timestamps and may be biased by missing records, timezone quality, or export scope. The report includes sample counts and does not infer a cause from correlation.
- Topic labels are keyword indicators, not verified root causes. Bonus/withdrawal policy decisions remain with a trained reviewer and approved policy source.
- The review tool records a caller-submitted note. The `reviewer` name and any approval are unverified: the tool does not authenticate the reviewer. Records are labelled `unverified` and are not proof of human approval. The MCP client's own approval prompts are the only confirmation step. The tool appends to a separate audit log and never alters the input export. Treat the log as sensitive operational data.
- Keep raw exports, `.env` files, review logs, and generated ticket reports out of source control.

## Checks

```powershell
python -m pytest --cov=support_triage --cov-report=term-missing
```

The test suite uses synthetic fixtures only (17 tests, 85% coverage).

Real-export run: the export is in the local folder `bf66c640cc851ef616bfad90e4822573/` (a git clone, gitignored, not committed). `artifacts/open_tickets_report.md` was generated from `tickets.json` with `--as-of 2026-09-29T09:00:00Z`. It covers 15 open tickets from a 30-ticket sample; the export README says it is not the full queue. The first-reply sample is 15 closed tickets, with a median of 4.58 hours and 0% within one hour. The export is fictional but is still kept out of the repo.

## MCP concepts in this build

Claude is the MCP host/client. It discovers the server's typed tool schemas, chooses a tool based on the user's request, and sends a structured call over stdio. The server validates inputs and executes local Python functions; tool results return to Claude for interpretation. MCP standardizes discovery and invocation, not the correctness or authority of business decisions. The human review gate and local-only boundary are therefore part of this tool's design, not something MCP itself guarantees.