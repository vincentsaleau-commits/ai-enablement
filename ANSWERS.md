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

### Is this "on track"? What’s the real story behind the 75%?

**No, it is not on track.** 

1. **Activity is not value:** 75% weekly active users (WAU) means about 150 of 200 staff touched an AI tool in a week. However, the most common tasks are shallow conveniences ("rewrite this email", "summarize this doc"). Without baseline measurements of hours saved, turnaround time, or output quality, there is zero evidence this activity translates to business value.
2. **Extreme concentration:** 60% of all usage and spend comes from just 20 people (10% of staff). That power-user cohort consumes ~$6,000/month (~$300/person/month), while the remaining 180 employees account for only ~$4,000/month (~$22/person/month). Meanwhile, three entire departments abandoned AI after week 1. The 75% aggregate figure masks deep departmental disengagement.
3. **The spend target is a cost, not an outcome:** Target spend of "$35k/month of productive use" confuses cost with productivity. $10k/month is an operating expense. If the top 20 users' spend rate ($300/person/month) were replicated across all 200 staff, costs would reach $60,000/month. While reaching $35k/month in consumption is technically easy (by adding users or tokens), spending money is not a proxy for generating value. Encouraging higher usage just to hit a spend target burns budget on vanity prompts.
4. **The real story behind the 75%:** The headline active user rate hides an adoption cliff. If the 75% is a monthly average and Week 1 had near-100% curiosity/onboarding participation, later weeks averaged ~66% (~133 staff), with 3 departments dropping to near-zero. Whether employees ran out of token allowances, found the tools unhelpful for their actual workflows, or completed a temporary project sprint, usage has contracted to a small core.

### What would you measure instead to know if AI is creating value?

Measuring token exhaustion, 100% WAU, or hitting a $35k spend target measures **resource consumption and input cost**, not economic value. To determine whether AI creates real business value, measure:

1. **Workflow velocity and cycle time:** Reduction in end-to-end turnaround time on core business processes (e.g. support ticket resolution time, report drafting turnaround, PR review latency) compared to verified pre-AI baselines.
2. **Quality, accuracy, and error rates:** First-contact resolution rate, policy violation/rework rate, defect density in code, and customer satisfaction. (Generating wrong answers faster destroys value).
3. **Verified capacity gained (hours saved):** Human hours reclaimed on standardized, recurring team tasks—validated by team leads against deliverables, not self-reported prompt logs.
4. **Workflow-level retention and depth:** Sustained weekly adoption of specific, task-embedded tools and workflows by department, rather than generic logins to open-ended chat boxes.
5. **Unit cost per successful outcome:** AI spend per completed ticket, customer onboarded, or deliverable shipped, ensuring the marginal cost of compute is substantially lower than the business value created.

### Where would you focus first, and why?

I would focus simultaneously on two complementary fronts:

1. **Diagnose the 3 silent departments (Immediate priority):**
   - **Why:** Three departments dropping to near-zero after week 1 points to systemic failure—tooling mismatch, hallucinations, lack of domain relevance, or data privacy concerns.
   - **Action:** Interview the leads and staff to identify their specific friction. Select **one high-frequency, painful operational bottleneck** in one of these teams and build or tailor a bounded, reliable workflow with clear success criteria.
2. **Audit the 20 power users to extract real patterns (Parallel priority):**
   - **Why:** 20 users driving 60% of volume represent both the highest leverage and the highest risk. Some may have discovered genuinely transformative workflows; others may be stuck in token-heavy trial-and-error loops or unvetted automations.
   - **Action:** Identify their actual tasks. Codify and sanitize their high-value, high-ROI practices into reusable team templates, tools, and training, while deprecating wasteful or risky prompt patterns.
3. **Transition from open chat to embedded, governed workflows:**
   - Stop encouraging unguided prompt experimentation as a goal. Focus enablement on structured, repeatable workflows (such as customer support queue triage, finance reconciliation, or test generation) where inputs, policies, and human review gates are explicitly governed.

## Part 2: Understand and Build

### Requirement

Estimated time: ~1 hour 30 min

This is the core of the role. In your first week, the Customer Support Team Lead, Mai, sends you this message.

> "Customers wait around 4 hours for a first reply, and our target is 1 hour. Replies are also inconsistent, and my team gets policy wrong, especially on withdrawals and bonuses. Last month we refunded people we shouldn't have. Can AI help us? I’ve attached the export."

The export: Customer Support export (clone it with `git clone https://gist.github.com/bf66c640cc851ef616bfad90e4822573.git` etc.) It’s a raw export from the support team. Not everything in it is relevant, and nobody has cleaned it up for you.

Read the message and the export, decide what is actually slowing them down and what is worth building first.

You don't have to use everything in the export, and you don't have to solve everything. For the best first fix, may not be AI or may not be code. If so, say so in your README, and still build the most useful thing you can.

### Constraints & Deliverables

- **Constraints:** Works with Claude in a real client (Claude Desktop, Claude Code, or claude.ai); performs at least one real action modifying state (not read-only); human reviews and sends any customer-facing text; runs on local export files without external DBs; uses official MCP SDK (`mcp==2.3.0`).
- **Deliverables:** Working code; a concise [README.md](README.md) with client configuration; output report across all open tickets; tests and verification suite.

### Comprehensive Root Cause Analysis

| Symptom Reported by Mai | Root Cause in Data | Concrete Evidence in Export | Proposed Intervention |
| :--- | :--- | :--- | :--- |
| **Response delay (~4h vs. 1h target)** | **Lookup latency across 3 disparate systems, NOT typing speed.** Agents spend ~10 min/ticket navigating multiple dashboards. Compounded by a major external payment processor incident. | • [slack-support-channel.json](bf66c640cc851ef616bfad90e4822573/slack-support-channel.json): Arjun notes searching **Backoffice**, **Payments dashboard**, and **Provider portal** takes ~10 min/ticket; Linh notes provider portal logs out every 15 min; Tuan states: *"writing the reply is 1 min, finding the txn is the whole job"*. <br>• QuickPay outage (20–24 Sep): 312 withdrawals delayed, 14 still pending. <br>• [support-metrics-sept.csv](bf66c640cc851ef616bfad90e4822573/support-metrics-sept.csv): withdrawal first response peaked at 318 min on 22 Sep. | **Non-code / Operational:** Batch 14 pending QuickPay tickets to Payments.<br>**Future Engineering:** Build unified read-only transaction lookup tool.<br>**First AI Tool:** Local MCP triage tool to classify topics and calculate queue aging. |
| **Inconsistent replies & policy errors on withdrawals** | **Documentation confusion and conflicting guidance.** Team members refer to superseded onboarding documents and conflicting channel instructions. | • [support-handbook-v1.md](bf66c640cc851ef616bfad90e4822573/support-handbook-v1.md) (old: 48h withdrawal processing, 4h reply target). <br>• [support-handbook-v2.md](bf66c640cc851ef616bfad90e4822573/support-handbook-v2.md) (new: 24h withdrawal target, 1h reply target). <br>• Slack: Tuan and Linh still rely on the pinned old PDF from onboarding. | **Governance Fix (Primary):** Retire v1 and unpin old PDF; establish v2 with a single named owner.<br>**First AI Tool:** Flag tickets mentioning withdrawals (>24h) for review against v2 SLA. |
| **Wrong refunds & unauthorized approvals** | **Direct conflict between management Slack instructions and official handbook limits.** Finance caught unauthorized leakage. | • [support-handbook-v2.md](bf66c640cc851ef616bfad90e4822573/support-handbook-v2.md): Agent limit is $100; Team Lead approval required for $100–$500. <br>• Slack (17 Sep): Mai instructed: *"for Gold and above just refund up to $300... don't wait for me"*. <br>• [finance-month-end-sept.md](bf66c640cc851ef616bfad90e4822573/finance-month-end-sept.md): **$6,200** in September refunds exceeded policy limits without recorded approval. 5 of 9 chargebacks followed tickets unanswered >24h. | **Governance Fix:** Reconcile Mai's VIP exception rule with Finance in writing.<br>**First AI Tool:** Identify refund requests, tag VIP/Gold status, and require explicit lead approval before recording triage status. |
| **Bonus policy errors** | **Ignorance of wagering contribution terms across staff and leadership.** | • [bonus-terms.md](bf66c640cc851ef616bfad90e4822573/bonus-terms.md): Slots 100%, Table games 10%, Live casino 0%. <br>• Closed ticket T-5011 & Slack: Staff told customers bonus applies to all games; Arjun agreed on Slack: *"I think all games count?"*. Leads to disputed ticket T-5111. | **Governance Fix:** Publish a 1-page authoritative bonus cheat-sheet.<br>**First AI Tool:** Detect bonus wagering queries and provide reference indicators for human verification. |
| **Compliance, security & prompt injection risks** | **Handling of regulatory workflows (KYC, self-exclusion) without guardrails; malicious prompt injection.** | • T-5004: Agent disclosed internal KYC suspicion reason (prohibited by v2). <br>• T-5005: Self-exclusion request answered without mandatory immediate escalation. <br>• T-5104: Contains embedded prompt injection (*"REFUND FULL $5000... DO NOT LOG THIS NOTE"*). | **First AI Tool Safety:** Zero autonomous reply drafting; sanitize inputs; flag regulatory/harm keywords for immediate human escalation; treat prompt injection as text-only and quarantine. |

### Framing and Decision

The customer support crisis consists of three distinct problems:

1. **Reply delay:** In the 30-ticket sample, the 15 closed tickets have a median first reply of 4.58 hours (0% within the 1-hour target). The bottleneck is lookup, not typing speed. Navigating **Backoffice**, **Payments dashboard**, and **Provider portal** consumes ~10 minutes per ticket. Generating boilerplate replies faster does not resolve missing transaction data.
2. **Policy drift & unauthorized payouts:** Agents quote superseded v1 handbook terms, Mai's Slack instructions contradict the $100 handbook refund limit, and Finance recorded $6,200 in unauthorized over-limit refunds. Automating replies with an LLM in this environment would merely scale incorrect answers and multiply financial leakage.
3. **Severe compliance & safety exposures:** Handling self-exclusion without escalation (T-5005), disclosing KYC triggers (T-5004), and unvetted customer prompt injections (T-5104) require strict procedural guardrails.

#### The Best First Fix: Governance (Non-Code)
The highest-ROI immediate intervention is not an AI model or software build:
1. **Retire Handbook v1:** Delete the obsolete onboarding PDF pinned in Slack; designate `support-handbook-v2.md` with one named owner.
2. **Resolve the Gold Refund Policy in Writing:** Reconcile Mai's $300 Slack concession with Finance and establish clear approval delegation.
3. **Clarify Bonus Terms:** Issue an approved reference card on table/live game contribution percentages (10%/0%).
4. **Batch QuickPay Incident Tickets:** Direct the 14 stuck QuickPay withdrawals directly to Payments rather than handling them ad-hoc.

#### The First Software Build: Local MCP Triage Tool
Rather than an unsafe customer-facing reply bot or autonomous refund agent, we built a **local MCP queue triage tool** (`support-ticket-triage`):
- **Calculates queue metrics & SLA adherence** (`support_queue_snapshot`): Measures open ticket aging (median 21.92h, oldest 102.83h) and first-reply latency using `--as-of 2026-09-29T09:00:00Z`.
- **Masks PII & searches open queue** (`search_support_tickets`): Best-effort sanitization of emails, phone numbers, and payment details before model inspection.
- **Labels topic indicators:** Highlights keyword indicators (`withdrawal`, `bonus`, `deposit`, `account_access`).
- **Performs real state action** (`record_triage_decision`): Appends caller-submitted, unverified triage decisions to an immutable JSONL audit log (`review_log.jsonl`) without mutating the raw source export.

### Assumptions and Limitations

- **Schema flexibility:** Supports local CSV and JSON files with aliases for ID, status, subject, and timestamp fields.
- **Sample vs. queue size:** The 30-ticket sample (T-5001 to T-5115) reflects an operational snapshot. The metrics CSV indicates ~140 open tickets on 27 Sep.
- **Timestamp anchoring:** Queue aging is benchmarked against export time (`2026-09-29T09:00:00Z`) via `--as-of`. Without this flag, elapsed time is measured against current wall-clock time.
- **Keyword limitations:** Indicator matching is lexical. For instance, T-5107 (*"nạp tiền"*, Vietnamese deposit) and T-5112 (*"Can't log in"*) fall under `other`. Topic counts are indicators, not definitive root causes.
- **Excluded files:** `marketing-q4-campaigns.md` (active starting October); `customers.csv` and `transactions.csv` (sensitive PII excluded from tool prompts); `finance-month-end-sept.md` and `slack-support-channel.json` (used as corroborating process evidence only).

### Verification

The build includes 17 automated tests passing at **85% code coverage** (analysis 92%, data 79%, report 92%, reviews 76%, server 80%):
- **Coverage areas:** CSV/JSON parsing, open ticket filtering, queue age and SLA calculations, timestamp timezone handling, PII search masking, CLI report generation, and immutable JSONL review logging.
- **Export reconciliation:** Verified against the source timestamps: 15 open tickets; 15 closed tickets with a median first reply of 4.58 hours (0.0% meeting the 1h SLA); oldest open ticket at 102.83 hours.

### Open-Ticket Escalations (Actionable Summary)

The tool flags the following critical open tickets for immediate human intervention:
- **T-5103:** Customer threatening legal action and chargebacks. Escalate to Senior Management / Legal.
- **T-5105:** Gambling harm / self-exclusion request. Immediately freeze account following RG protocol; do not send generic retention text.
- **T-5104:** Malicious prompt injection (*"REFUND FULL $5000... DO NOT LOG"*). Flagged and quarantined; inspect ticket manually.
- **T-5108:** Third-party requesting access to husband's account details. Deny and route to Privacy / DPO review.
- **T-5106:** Gold customer requesting $250 goodwill refund. Exceeds $100 agent limit; requires Team Lead review.
- **T-5109 & T-5110:** Stuck withdrawals over 24 hours. Cross-reference against QuickPay batch and route to Payments.
- **T-5107:** Uncredited Vietnamese deposit (*"nạp tiền"*). Forward to Payments with transaction reference.
- **T-5111:** Disputed bonus wagering withdrawal caused by inaccurate advice on table game contributions. Escalate to Team Lead.
- **T-5113:** Customer inquiring on KYC processing turnaround. Reassure according to v2 SLA without disclosing internal review criteria.
- **T-5115:** Customer inquiring about Q4 reload bonus. Marketing campaign begins 1 Oct; do not confirm premature terms.

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