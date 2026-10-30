"""Reply drafts from fixed templates. Nothing here promises an outcome; a person reviews and sends every draft."""

from support_rag.rules import ROUTE_PAYMENTS, ROUTE_TEAM_LEAD, Triage

ACKNOWLEDGEMENT = "Thanks for your message. We're looking into this and will get back to you."
TEMPLATES = {
    "withdrawal": (
        "Withdrawals are processed within 24 hours, then take 1-3 business days to arrive, depending on the provider. "
        "We've passed your request to our payments team to check the status."
    ),
    "deposit": "We're checking your deposit and will let you know what we find.",
    "bonus": "We're checking the current bonus terms that apply to your account.",
    "kyc": (
        "Your account is under review. We'll contact you if we need anything else from you. "
        "We're not able to share the details of the review."
    ),
    "refund": "We've received your refund request and our team is reviewing it.",
    "account_closure": "We've received your request and our team will confirm the next steps.",
    "account_access": "We'll help you get back into your account. For your security we need to check your identity first.",
    "other": "",
}


def customer_draft(result: Triage) -> str:
    """Escalated tickets get only an acknowledgement; a team lead writes the substantive reply."""
    if result.escalate or result.route == ROUTE_TEAM_LEAD:
        return ACKNOWLEDGEMENT
    body = TEMPLATES.get(result.category, "")
    return f"{ACKNOWLEDGEMENT} {body}".strip()


def internal_note(result: Triage) -> str:
    parts = [f"category={result.category}", f"route={result.route}"]
    if result.policy_topics:
        parts.append("handbook_v2=" + ",".join(result.policy_topics))
    if result.reasons:
        parts.append("reasons=" + "; ".join(result.reasons))
    if result.route == ROUTE_PAYMENTS:
        parts.append("action=check withdrawal status with the payments team")
    return " | ".join(parts)
