"""Deterministic triage: category, risk flags, routing, and whether a person must decide.

No model is called and ticket text never leaves this process. Prompt-injection text is only detected here, not followed.
"""

import re
from dataclasses import dataclass

REFUND_LIMIT_USD = 100
ROUTE_AGENT = "agent"
ROUTE_PAYMENTS = "payments"
ROUTE_TEAM_LEAD = "team_lead"

INJECTION = re.compile(r"ignore (all )?(previous|prior) instructions|system note|to assistant", re.IGNORECASE)
GAMBLING_HARM = re.compile(
    r"can'?t stop|cannot stop|lost (way )?more than|self[- ]?exclu|gambl|addict|can'?t control|let me back in",
    re.IGNORECASE,
)
LEGAL_OR_CHARGEBACK = re.compile(r"chargeback|lawyer|\blegal\b|\bsue\b|regulator", re.IGNORECASE)
FRAUD = re.compile(r"hacked|account takeover|unauthori[sz]ed|someone else (logged|accessed)", re.IGNORECASE)
OTHER_PERSON = re.compile(
    r"my (husband|wife|partner|boyfriend|girlfriend|son|daughter|brother|sister|mother|father)"
    r"|his account|her account|their account|shared account|share everything|\b\w+@\w+\.\w+",
    re.IGNORECASE,
)
ACCOUNT_ACCESS = re.compile(r"log ?in|2fa|two[- ]factor|lost my phone|locked out|password", re.IGNORECASE)
NOT_IN_HANDBOOK = re.compile(r"reload bonus|bank transfer|deposit method|payment method", re.IGNORECASE)
WITHDRAWAL_DELAY = re.compile(
    r"pending|stuck|hasn'?t (arrived|reached)|still no|not (arrived|reached|here|there)|isn'?t (here|there)"
    r"|still waiting|still not|haven'?t received",
    re.IGNORECASE,
)
REOPEN = re.compile(r"reopen|re-open|unblock|unlock my account", re.IGNORECASE)
REFUND_REQUEST = re.compile(r"refund|money back|want my money|lost my bet|hoàn tiền", re.IGNORECASE)
KYC_WORDS = re.compile(r"verif|kyc|passport|identity", re.IGNORECASE)
AMOUNT = re.compile(r"\$\s?([\d,]+(?:\.\d{1,2})?)")

# Checked in order: the first match decides the category. Vietnamese keywords included for customer messages.
CATEGORY_RULES = (
    ("withdrawal", re.compile(r"withdr|rút|cash ?out", re.IGNORECASE)),
    ("deposit", re.compile(r"deposit|nạp", re.IGNORECASE)),
    ("bonus", re.compile(r"bonus|thưởng", re.IGNORECASE)),
    ("kyc", re.compile(r"verif|kyc|passport|documents?", re.IGNORECASE)),
    ("refund", re.compile(r"refund|money back|lost my bet|froze|crash", re.IGNORECASE)),
    ("account_closure", re.compile(r"close my account|delete my account", re.IGNORECASE)),
    ("account_access", ACCOUNT_ACCESS),
)
TOPICS = {
    "withdrawal": ("withdrawals",),
    "deposit": ("deposits",),
    "bonus": ("bonuses",),
    "kyc": ("kyc",),
    "refund": ("refunds",),
    "account_closure": ("escalation",),
    "account_access": ("privacy", "escalation"),
}


@dataclass(frozen=True)
class Triage:
    category: str
    escalate: bool
    route: str
    reasons: tuple[str, ...]
    policy_topics: tuple[str, ...]
    amount_usd: float | None
    retrieval_topics: tuple[str, ...] = ()


# Reasons that point to a risk or an unclear policy, so the note should read only the escalation section.
ESCALATION_ONLY_MARKERS = (
    "not sure which policy",
    "reopening",
    "self-excluded",
    "gambling harm",
    "legal or chargeback",
    "suspected fraud",
)


def largest_amount(text: str) -> float | None:
    amounts = [float(match.replace(",", "")) for match in AMOUNT.findall(text)]
    return max(amounts) if amounts else None


def classify_category(text: str) -> str:
    for category, pattern in CATEGORY_RULES:
        if pattern.search(text):
            return category
    return "other"


def triage(subject: str, message: str, self_excluded: bool = False) -> Triage:
    text = f"{subject}\n{message}".strip()
    reasons: list[str] = []

    if not message.strip():
        reasons.append("empty message")
    if self_excluded:
        reasons.append("customer is self-excluded; follow the self-exclusion process")
    if INJECTION.search(text):
        reasons.append("text tries to instruct the assistant")
    if GAMBLING_HARM.search(text):
        reasons.append("possible gambling harm; follow the self-exclusion process")
    if LEGAL_OR_CHARGEBACK.search(text):
        reasons.append("legal or chargeback threat")
    if FRAUD.search(text):
        reasons.append("suspected fraud or account takeover")
    if OTHER_PERSON.search(text):
        reasons.append("request about another person's account (privacy)")
    if REOPEN.search(text):
        reasons.append("account reopening needs team lead approval")

    category = classify_category(text)
    amount = largest_amount(text)
    if category == "refund" and amount is not None and amount > REFUND_LIMIT_USD:
        reasons.append(f"refund of ${amount:,.0f} is above the ${REFUND_LIMIT_USD} agent limit")
    if REFUND_REQUEST.search(text) and amount is None:
        reasons.append("refund requested without an amount; team lead must confirm it is within the agent limit")
    if category == "account_access":
        reasons.append("account access needs identity checks before any change")
    if re.search(r"bonus|thưởng", text, re.IGNORECASE) and re.search(r"withdr|rút", text, re.IGNORECASE):
        reasons.append("bonus withdrawal depends on wagering rules; check the current terms")
    topics = list(TOPICS.get(category, ()))
    if KYC_WORDS.search(text) and "kyc" not in topics:
        topics.append("kyc")
    if NOT_IN_HANDBOOK.search(text):
        reasons.append("not covered by the current handbook or bonus terms")
    if category == "other":
        reasons.append("not sure which policy applies")

    route = ROUTE_AGENT
    if category == "withdrawal" and WITHDRAWAL_DELAY.search(text):
        route = ROUTE_PAYMENTS
    if reasons:
        route = ROUTE_TEAM_LEAD
    return Triage(
        category=category,
        escalate=bool(reasons),
        route=route,
        reasons=tuple(reasons),
        policy_topics=tuple(topics),
        amount_usd=amount,
        retrieval_topics=retrieval_topics(topics, reasons),
    )


def retrieval_topics(topics: list[str], reasons: list[str]) -> tuple[str, ...]:
    """Which policy sections the model may read. Tickets escalated for a specific risk read only the escalation section.

    Without this, a blocked-account or complaint ticket is matched to the 'failed deposit' paragraph simply because it
    mentions deposits, and the note then discusses the wrong problem.
    """
    if any(marker in reason for reason in reasons for marker in ESCALATION_ONLY_MARKERS):
        topics = ["escalation"]
        if any("bonus" in reason for reason in reasons):
            topics.append("bonuses")
        return tuple(topics)
    if any("bonus" in reason for reason in reasons) and "bonuses" not in topics:
        topics.append("bonuses")
    if any("privacy" in reason for reason in reasons):
        # Another person's account is answered from the privacy rules, not from the withdrawal timelines.
        return ("privacy", "escalation")
    return tuple(topics)
