"""Decisions and checks that the language model cannot override.

The rules in support_rag.rules decide escalation, routing and refund authority. The model only writes an internal
note from retrieved evidence, and every number in that note must appear in the ticket or the evidence.
"""

import re
from dataclasses import dataclass

from support_rag.drafts import customer_draft
from support_rag.rules import ROUTE_PAYMENTS, ROUTE_TEAM_LEAD, Triage, triage

ACTION_ESCALATE = "escalate_to_team_lead"
ACTION_PAYMENTS = "route_to_payments"
ACTION_TEMPLATE = "reply_with_template"
ACTIONS = (ACTION_ESCALATE, ACTION_PAYMENTS, ACTION_TEMPLATE)
NUMBER = re.compile(r"\d[\d,.]*")
EVIDENCE_ID = re.compile(r"\bE\d+\b")
# File names such as support-handbook-v2.md, version tags such as v2, and evidence IDs are labels, not amounts.
NON_VALUE_LABEL = re.compile(r"[\w-]+\.(?:md|csv|json|txt)\b|\bv\d+\b|\bE\d+\b", re.IGNORECASE)


@dataclass(frozen=True)
class Decision:
    triage: Triage
    action: str
    customer_draft: str


def decide(subject: str, message: str, self_excluded: bool = False) -> Decision:
    result = triage(subject, message, self_excluded)
    if result.escalate or result.route == ROUTE_TEAM_LEAD:
        action = ACTION_ESCALATE
    elif result.route == ROUTE_PAYMENTS:
        action = ACTION_PAYMENTS
    else:
        action = ACTION_TEMPLATE
    return Decision(triage=result, action=action, customer_draft=customer_draft(result))


NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}
NUMBER_WORD = re.compile(r"\b(" + "|".join(NUMBER_WORDS) + r")\b", re.IGNORECASE)


def numbers_grounded(note: str, allowed_texts: list[str]) -> bool:
    """True when every number the note mentions also appears in the ticket or the evidence excerpts.

    Number words count as their digits, so "two days" in a ticket supports "2 days" in a note.
    """
    allowed = NUMBER_WORD.sub(lambda m: NUMBER_WORDS[m.group(1).lower()], " ".join(allowed_texts))
    allowed_numbers = {n.strip(".,") for n in NUMBER.findall(allowed)}
    note_without_labels = NON_VALUE_LABEL.sub("", note)
    return all(n.strip(".,") in allowed_numbers for n in NUMBER.findall(note_without_labels))


SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
CONTENT_WORD = re.compile(r"[a-z]{4,}")
STOP_WORDS = frozenset({"that", "this", "with", "from", "have", "will", "they", "their", "there", "about", "customer"})


MIN_SENTENCE_SUPPORT = 0.6
COPY_RUN_WORDS = 12


def unsupported_sentences(note: str, allowed_texts: list[str]) -> list[str]:
    """Sentences where fewer than MIN_SENTENCE_SUPPORT of the content words appear in the ticket or evidence."""
    allowed_words = set(CONTENT_WORD.findall(" ".join(allowed_texts).lower()))
    flagged = []
    for sentence in SENTENCE_BOUNDARY.split(NON_VALUE_LABEL.sub("", EVIDENCE_ID.sub("", note))):
        words = set(CONTENT_WORD.findall(sentence.lower())) - STOP_WORDS
        if not words:
            continue
        support = len(words & allowed_words) / len(words)
        if support < MIN_SENTENCE_SUPPORT:
            flagged.append(sentence.strip())
    return flagged


TIMELINE = re.compile(
    r"(\d+(?:\s*[-–]\s*\d+)?)\s*(?:business\s+)?(hours?|days?)\b(\s+ago)?|\b(same|next)\s+(day)\b",
    re.IGNORECASE,
)
# Decision and rule phrases the model must not invent. A claim passes only if the same phrase is in the policy evidence.
DECISION_CLAIM = re.compile(
    r"\b(not eligible|eligible|entitled|cannot be approved|can be approved|cannot be processed|will be refunded"
    r"|approved|not refundable|refundable|future reloads?|retroactively|will be available|announced|scheduled"
    r"|reopen(?:ed|ing)?)\b",
    re.IGNORECASE,
)
# An internal note is not a customer letter. Salutations and sign-offs mean the model copied a reply.
LETTER_STYLE = re.compile(r"\b(dear|best regards|sincerely|kind regards)\b", re.IGNORECASE)
# "It's been 6" in a ticket means six days: the customer's own elapsed time, without a unit.
TICKET_BEEN_DAYS = re.compile(r"\bbeen\s+(\d+)\b(?!\s*(?:hours?|days?|business))", re.IGNORECASE)
# Words near a timeline that show it describes the customer's own elapsed time, not a policy deadline.
ELAPSED_CONTEXT = re.compile(r"\b(ago|since|waiting|been|still|pending|stuck|delayed)\b", re.IGNORECASE)


def _timelines(text: str) -> set[tuple[str, str, bool]]:
    found = set()
    for number, unit, ago, word, word_unit in TIMELINE.findall(text):
        if word:
            found.add((f"{word.lower()}-day", word_unit.lower(), False))
        else:
            found.add((re.sub(r"\s+", "", number).replace("–", "-"), unit.lower().rstrip("s"), bool(ago)))
    return found


def _match_key(match: re.Match) -> tuple[str, str, bool]:
    if match.group(4):
        return f"{match.group(4).lower()}-day", "day", False
    number = re.sub(r"\s+", "", match.group(1)).replace("–", "-")
    return number, match.group(2).lower().rstrip("s"), bool(match.group(3))


def timelines_grounded(note: str, evidence_texts: list[str], ticket_text: str = "") -> bool:
    """True when every timeline in the note is supported.

    A plain timeline ("within 4 days") must appear in the policy evidence. A timeline that matches the ticket may be
    used only when it describes the customer's own elapsed time ("2 days ago", "waiting 6 days").
    """
    evidence = {(number, unit) for number, unit, _ in _timelines(" ".join(evidence_texts))}
    ticket = {(number, unit) for number, unit, _ in _timelines(ticket_text)}
    ticket |= {(number, "day") for number in TICKET_BEEN_DAYS.findall(ticket_text)}
    for match in TIMELINE.finditer(note):
        number, unit, ago = _match_key(match)
        if (number, unit) in evidence:
            continue
        window = note[max(0, match.start() - 40): match.end() + 40]
        if (number, unit) in ticket and (ago or ELAPSED_CONTEXT.search(window)):
            continue
        return False
    return True


def decision_claims_grounded(note: str, evidence_texts: list[str]) -> bool:
    """True when every eligibility or approval word in the note also appears in the policy evidence."""
    evidence = " ".join(evidence_texts).lower()
    return all(claim.lower() in evidence for claim in DECISION_CLAIM.findall(note))


def reads_as_letter(note: str) -> bool:
    return bool(LETTER_STYLE.search(note))


def copies_ticket(note: str, ticket_message: str) -> bool:
    """True when the note repeats a long run of the customer's own words instead of summarising policy."""
    note_words = re.findall(r"[a-z']+", note.lower())
    message_words = re.findall(r"[a-z']+", ticket_message.lower())
    if len(message_words) < COPY_RUN_WORDS:
        return False
    message_runs = {
        tuple(message_words[i:i + COPY_RUN_WORDS]) for i in range(len(message_words) - COPY_RUN_WORDS + 1)
    }
    return any(tuple(note_words[i:i + COPY_RUN_WORDS]) in message_runs for i in range(len(note_words) - COPY_RUN_WORDS + 1))
