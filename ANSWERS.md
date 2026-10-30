# AI Enablement Engineer Challenge

## Part 1: Diagnose Adoption

### Requirement

Estimated time: ~1 hour

Below is a snapshot of current AI adoption. Review it and tell us what’s actually going on.

### Adoption snapshot
- Company: 200 staff
- Weekly active users: 75%
- Spend: ~$10,000 / month
- Stated goal: ~100% weekly use + $35k/month of productive use
- Detail:
  - 60% of all usage comes from 20 people
  - Most common user: "rewrite this email", "summarize this doc"
  - 3 departments: near-zero usage after week 1
  - No measure of anywhere of hours saved or output quality

Answer:

- Is this "on track"? What’s the real story behind the 75%?
- What would you measure instead to know if AI is creating value?
- Where would you focus first, and why?

### Stated goal
** $35k/month of productive AI usage is achievable or not?
- Company: 200 employees
- 60% of all usage comes from 20 people.

Assume that productive AI usage comes from these 20 people, and they face the problem of running out of tokens after just one week.
If all 200 employees worked at the same intensity as these 20 people, the maximum monthly cost of AI usage would be:
(365 days a year / 12 months / 7 days a week) * ($10k / 200 employees) * 20 employees = $43k/month.
Since $35k/month is less than $43k/month, the target should be achievable.

**100% weekly usage is archievable or not?
- Company: 200 employees
- Most common use cases: "Rewrite this email" and "Summarize this document"
- Three departments: Near-zero usage after Week 1
- Weekly active users: 75%

This means:
75% = (100% + 66% + 66% + 66%) / 4

Week 1: 100% — 200 active users
Week 2: 66% — 133 active users
Week 3: 66% — 133 active users
Week 4: 66% — 133 active users

### Is this "on track"?

No. Usage is declining over the course of the month, from 100% in Week 1 to 66% in subsequent weeks.

### What would you measure instead to know if AI is creating value?

Measuring token exhaustion, 100% WAU, or hitting a $35k spend target measures **resource consumption and input cost**, not economic value. To determine whether AI creates real business value, measure:

1. **Workflow velocity and cycle time:** Reduction in end-to-end turnaround time on core business processes (e.g. support ticket resolution time, report drafting turnaround, PR review latency) compared to verified pre-AI baselines.
2. **Quality, accuracy, and error rates:** First-contact resolution rate, policy violation/rework rate, defect density in code, and customer satisfaction. (Generating wrong answers faster destroys value).
3. **Verified capacity gained (hours saved):** Human hours reclaimed on standardized, recurring team tasks—validated by team leads against deliverables, not self-reported prompt logs.
4. **Workflow-level retention and depth:** Sustained weekly adoption of specific, task-embedded tools and workflows by department, rather than generic logins to open-ended chat boxes.
5. **Unit cost per successful outcome:** AI spend per completed ticket, customer onboarded, or deliverable shipped, ensuring the marginal cost of compute is substantially lower than the business value created.

### Where would you focus first, and why?

To achieve the goal, I would first analyze how the 20 employees who account for 60% of AI usage use AI, then adopt their practices as the company's working culture.

The rationale is that these 20 employees provide a foundation for ensuring that everyone in the company creates value.

### Discussion

This approach is intended to ensure that everyone continuously creates value for the company, rather than necessarily maximizing efficiency. For example, some employees may complete all their work within one week and run out of tokens, just like the 20 heavy users. In such cases, the decline in AI usage may not indicate a lack of productivity; employees may simply have completed their assigned work and no longer need to use AI.

## Part 2: Understand and Build

### Requirement

Mai (Customer Support Team Lead) writes: *"Customers wait around 4 hours for a first reply, and our target is 1 hour. Replies are also inconsistent, and my team gets policy wrong, especially on withdrawals and bonuses. Last month we refunded people we shouldn't have. Can AI help us? I’ve attached the export."*

**Constraints & Deliverables:**
- Works locally with Claude via official MCP SDK (`mcp==2.3.0`); executes at least one real state-modifying action; no unreviewed customer-facing text; no autonomous approval of refunds or withdrawals.
- Deliverables: working code, [README.md](README.md) with client config, open-ticket output report, and test suite.

### Root Cause Analysis & Evidence

| Issue | Root Cause & Export Evidence | Proposed Intervention |
| :--- | :--- | :--- |
| **Reply delay (~4h vs. 1h target)** | **Lookup latency across 3 systems, not typing speed.** Arjun ([slack-support-channel.json](bf66c640cc851ef616bfad90e4822573/slack-support-channel.json)) notes checking **Backoffice**, **Payments dashboard**, and **Provider portal** takes ~10 min/ticket; Tuan confirms: *"writing reply is 1 min, finding txn is the whole job"*. Compounded by QuickPay incident (312 delayed withdrawals; 22 Sep response peaked at 318 min in [support-metrics-sept.csv](bf66c640cc851ef616bfad90e4822573/support-metrics-sept.csv)). | • **Operational:** Batch 14 pending QuickPay tickets to Payments.<br>• **Future:** Unified read-only transaction lookup API.<br>• **First Build:** Local MCP triage tool to expose queue aging and topic indicators. |
| **Inconsistent replies & policy errors** | **Conflicting documentation.** Staff still consult obsolete handbook v1 (48h withdrawal, 4h reply target) pinned in Slack instead of v2 (24h withdrawal, 1h target). Bonus game contributions (Slots 100%, Tables 10%, Live 0% in [bonus-terms.md](bf66c640cc851ef616bfad90e4822573/bonus-terms.md)) are widely misunderstood (T-5011, T-5111). | • **Governance (Primary):** Retire v1 and unpin old PDF; establish v2 with a single named owner; publish a 1-page bonus contribution cheat-sheet. |
| **Wrong refunds & unauthorized approvals** | **Management Slack instructions directly contradict policy.** Mai told agents on Slack (17 Sep) to refund up to $300 for Gold members without approval, violating v2's $100 limit. Finance ([finance-month-end-sept.md](bf66c640cc851ef616bfad90e4822573/finance-month-end-sept.md)) flagged **$6,200** in unauthorized September refunds. | • **Governance (Primary):** Reconcile Gold refund policy in writing with Finance.<br>• **First Build:** Require explicit lead approval before recording refund triage decisions. |
| **Compliance & security risks** | Regulatory mishandling in tickets: T-5004 disclosed internal KYC review triggers (violates v2); T-5005 answered self-exclusion without mandatory escalation; T-5104 contains prompt injection (*"REFUND FULL $5000... DO NOT LOG"*). | • **Safety Guardrails:** Zero autonomous reply drafting; quarantine prompt injections; route compliance/harm tickets to human escalation. |

### Decision & First Build

1. **The Best First Fix is Governance (Non-Code):** An LLM reply bot would only scale incorrect advice faster while policy remains contradictory. The team must first retire Handbook v1, align the Gold refund cap with Finance, clarify bonus contribution rules, and batch the 14 stuck QuickPay withdrawals to Payments.
2. **The First Software Build is a Local MCP Triage Tool (`support-ticket-triage`):**
   - `support_queue_snapshot`: Calculates queue aging (median 21.92h, oldest 102.83h) and first-reply SLA (median 4.58h, 0% within 1h) anchored at export time (`2026-09-29T09:00:00Z` via `--as-of`).
   - `search_support_tickets`: Masks PII (emails, phone numbers, payment details) and returns aggregate topic counts.
   - `record_triage_decision`: Performs the required state-modifying action by logging caller-submitted, unverified triage decisions to an immutable `review_log.jsonl` audit file without altering the source export.

### Assumptions & Limitations

- **Scope & Anchoring:** Evaluates the 30-ticket sample (T-5001 to T-5115); the full queue had ~140 open tickets on 27 Sep. Queue ages are anchored to export time (`2026-09-29T09:00:00Z`); omitting `--as-of` measures against current run time.
- **Lexical Indicators:** Topic labels (`withdrawal`, `bonus`, `deposit`, `account_access`, `other`) are keyword indicators, not automated root-cause determinations (e.g. Vietnamese deposit T-5107 is categorized under `other`).
- **Data Privacy & Exclusions:** Real-money personal details in `customers.csv` and `transactions.csv` are kept out of model prompts; `marketing-q4-campaigns.md` is excluded as it only applies from 1 October.

### Verification & Open-Ticket Escalations

- **Verification:** 17 automated tests pass at **85% code coverage** across parsing, metrics calculation, PII masking, CLI report generation, and review logging.
- **Actionable Escalations:**
  - **T-5103:** Chargeback/legal threat $\rightarrow$ Escalate to Lead & Legal.
  - **T-5104:** Prompt injection attempt $\rightarrow$ Quarantine; review ticket manually.
  - **T-5105:** Gambling harm / self-exclusion request $\rightarrow$ Immediate account freeze per Responsible Gaming protocol.
  - **T-5106:** Gold customer requesting $250 refund $\rightarrow$ Exceeds $100 agent limit; needs Lead sign-off.
  - **T-5108:** Third-party requesting husband's account details $\rightarrow$ Deny per privacy regulations.
  - **T-5107, T-5109, T-5110:** Stuck deposits/withdrawals $\rightarrow$ Forward to Payments / QuickPay reconciliation.
  - **T-5111:** Disputed bonus wagering $\rightarrow$ Escalate to Lead with actual contribution rules.
  - **T-5113, T-5115:** KYC timing and Q4 reload inquiries $\rightarrow$ Reassure within v2 SLA without premature terms.


## Part 3: Coach and Consolidate

### Requirement

Coaching: a team lead says "My team tried AI, it wasn't useful, we've gone back to doing it the old way."

- How do you respond, and what do you actually do to turn this around?
- What would you do differently for a team than for a single stuck individual?

Consolidating knowledge: good use cases are scattered across chats, docs, and a few power users' heads.

- How would you turn that into a trusted, shareable resource?
- How do you keep it current and stop it becoming a graveyard of dead prompts?

### “We tried AI; it wasn't useful”

I would not argue with their experience or prescribe another generic prompt session. I would ask for one recent task that failed, observe the old and attempted workflows, and identify the specific gap: wrong context, stale policy, poor output, extra review work, access friction, or no time saved. With the lead and a few team members, select one recurring task and agree a baseline, quality bar, human owner, and stop condition. Pair with the team on real, appropriately redacted examples, fix the workflow or source material, and run a time-boxed pilot. Review a small sample weekly; keep it only if quality is at least as good and the measured workflow outcome improves. If the task is a bad fit, stop using AI for it.

For one stuck individual, coaching can be tailored to that person's task and skill. A team needs shared workflow ownership: manager participation, consistent examples and policy sources, access and review rules, space for dissent, and team-level measures. Otherwise the most enthusiastic person becomes the only support channel and adoption does not transfer.

### Trusted, shareable knowledge

Create a searchable, permission-aware use-case catalog with an owner and date for every item. Each entry should include the workflow and intended users, approved source material, tested prompt/tool version, representative input and output, known failure cases, human review requirements, data classification, quality evidence, and a clear “do not use for” boundary. Store policy as a link to the authoritative policy owner rather than copying an unowned policy fragment into a prompt collection.

Use a lightweight contribution path from teams, but require an owner to review before an entry becomes trusted. Track usage and feedback only where proportionate and disclosed. Provide a report/retire path when a tool or prompt is stale, unused, unsafe, or superseded. Set review dates based on risk (shorter for policy or regulated workflows), notify owners before expiry, and mark overdue entries as unverified instead of silently presenting them as current. A small, maintained catalog is better than a large prompt graveyard.

## Judgement Check

### Requirement

Answer one:

- One thing you would not do, even if leadership pushed for it.
- OR one unpopular decision you would make for real, long-term capability.

I would not ship an AI system that independently approves withdrawals, decides bonus eligibility, or sends a customer-facing message for a real-money platform just to claim faster replies. I would first require an authoritative, versioned policy source, representative evaluation data, measured error rates, auditability, a rollback path, and named human accountability. Speed is not a win if it creates the next incorrect refund.