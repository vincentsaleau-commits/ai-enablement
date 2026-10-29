# AI Enablement Engineer Challenge

## Purpose

This challenge is designed to assess how you read data and frame a vague problem, whether you can build AI tools that work and are safe, and how you get people to actually use them.

## Challenge Overview

You are joining 99Tech, a fast-growing technology company running high-traffic, real-money platforms for global clients.

We are pushing AI to be a default part of how every team works. Tools are available, but adoption is uneven — some people are power users, some teams have gone quiet, and a lot of usage is shallow. Your job is to find where work is slow or error-prone, build AI tools that fix it, and make sure people use them. You sit within AI Enablement and report to the AI & Innovation Manager. You are the technical owner of what you build, from first prototype to production. Where it helps, you work with engineering teams on implementation.

This brief is intentionally not a full specification. Where something is unclear, make a call and state your assumption.

Be direct.

On AI use: you are welcome to use AI coding tools; we use them every day. In the interview, we will ask how MCP and tool calling work using your own build as the example, walk through your code with you, and ask you to extend it live. Make sure you understand everything you submit.

---

## Part 1 — Diagnose Adoption

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

---

## Part 2 — Understand & Build

Estimated time: ~1 hour 30 min

This is the core of the role. In your first week, the Customer Support Team Lead, Mai, sends you this message.

> "Customers wait around 4 hours for a first reply, and our target is 1 hour. Replies are also inconsistent, and my team gets policy wrong, especially on withdrawals and bonuses. Last month we refunded people we shouldn't have. Can AI help us? I’ve attached the export."

The export: Customer Support export (clone it with `git clone https://gist.github.com/bf66c640cc851ef616bfad90e4822573.git` etc.) It’s a raw export from the support team. Not everything in it is relevant, and nobody has cleaned it up for you.

Read the message and the export, decide what is actually slowing them down and what is worth building first.

You don't have to use everything in the export, and you don't have to solve everything. For the best first fix, may not be AI or may not be code. If so, say so in your README, and still build the most useful thing you can.

### Constraints

- It works with Claude in a real client (Claude Desktop, Claude Code, or claude.ai).
- It does at least one real action on the data, not only reading it.
- If anything you build produces customer-facing text, a person reviews and sends it.
- It runs on the export as local files. No real systems needed.
- Any language. If you build an MCP server, use an official MCP SDK (TypeScript or Python recommended). Claude Skills are fine where they fit.

---

## What to include

- Your code.
- A short README: how to run it, including the client config, and a few lines on what you built.
- The output of running your tool on all open tickets.
- Any tests or checks you ran to make sure the output is correct.

---

## Part 3 — Coach & Consolidate

Estimated time: ~45 min

Coaching. One team lead tells you: "My team tried AI, it wasn't useful, we’ve gone back to doing it the old way."

- How do you respond, and what do you actually do to turn this around?
- What would you do differently for a team than for a single stuck individual?

Consolidating knowledge. Good use cases are scattered across chats, docs, and a few power users’ heads.

- How would you turn that into a trusted, shareable resource?
- How do you keep it current and stop it becoming a graveyard of dead prompts?

---

## Judgement Check (Required)

Answer one:

- One thing you would not do, even if leadership pushed for it
- OR one unpopular decision you would make for real, long-term capability

---

## How to Submit

Send us a link to one Git repository containing your Part 2 work and a single document with your answers to Part 1, Part 3, and the Judgement Check. Make sure we can access the repository.

---

## What We Are Evaluating

We are not looking for:

- Perfect or exhaustive answers
- Polished UX or create features
- Using everything in the export
- Buzzwords or framework name-dropping
- AI slop

We are looking for:

- Whether you read the adoption data honestly (activity vs value)
- How you framed the support problem, and what you chose to build first
- What you noticed in the export, and what you questioned
- Working code that runs in a real client, with tool design a model can reliably use
- How you checked your tool is right
- Practical, human coaching — you can meet people where they are
- A real plan to consolidate and maintain shared knowledge
- Direct writing with no fluff
