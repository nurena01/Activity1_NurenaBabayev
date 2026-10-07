"""Q1 - Spam Filter Email Agent.

The agent is a SIMPLE REFLEX AGENT. Its structure follows the textbook's
SIMPLE-REFLEX-AGENT pseudocode (AIMA 4th ed., Chapter 2):

    function SIMPLE-REFLEX-AGENT(percept) returns an action
        persistent: rules, a set of condition-action rules

        state  <- INTERPRET-INPUT(percept)
        rule   <- RULE-MATCH(state, rules)
        action <- rule.ACTION
        return action

Percept : the raw contents of one .eml file (bytes).
State   : what the agent observes in that email - the sender's domain and the
          number of bad words in the readable body text.
Rules   : condition-action rules, checked in priority order (first match wins).
Actions : MOVE_TO_EMAIL or MOVE_TO_SPAM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path
from typing import Callable, Iterable

MOVE_TO_EMAIL = "MoveToEmail"
MOVE_TO_SPAM = "MoveToSpam"

# "If more than 5 words within the body of the email are found on this list"
BAD_WORD_THRESHOLD = 5

DATA_DIR = Path(__file__).resolve().parent / "data"

WORD_PATTERN = re.compile(r"[^\W_]+")  # runs of letters/digits, including accented letters
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def load_list(path) -> set[str]:
    """Read one entry per line, lowercased. Blank lines and # comments are ignored."""
    entries = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            entries.add(line)
    return entries


@dataclass(frozen=True)
class EmailState:
    """The agent's interpretation of one percept (one email)."""

    sender_domain: str | None
    bad_word_count: int


@dataclass(frozen=True)
class Rule:
    """A condition-action rule: if condition(state) then action."""

    name: str
    condition: Callable[[EmailState], bool]
    action: str
    reason: str  # human-readable explanation, formatted with the state's fields


@dataclass(frozen=True)
class Decision:
    """The chosen action plus why it was chosen (used for printing and tests)."""

    action: str
    rule: Rule
    state: EmailState

    @property
    def reason(self) -> str:
        return self.rule.reason.format(
            sender_domain=self.state.sender_domain or "unknown",
            bad_word_count=self.state.bad_word_count,
        )


# ---------------------------------------------------------------------------
# Sensors: helpers used by INTERPRET-INPUT to read an email
# ---------------------------------------------------------------------------

def sender_domain(message) -> str | None:
    """Domain of the From: address, lowercased, or None if it cannot be read."""
    _, address = parseaddr(str(message.get("From", "")))
    if "@" not in address:
        return None
    domain = address.rsplit("@", 1)[1].strip().lower().rstrip(".")
    return domain or None


def readable_text(message) -> str:
    """Decoded text of every readable text/* part: the body and any text attachments.

    Non-text parts (images, binaries, encrypted payloads) are skipped because
    the agent cannot read them; this is why the environment is only
    partially observable.
    """
    return "\n".join(_text_parts(message))


def _text_parts(part):
    if part.get_content_type() == "multipart/alternative":
        # The same content in several formats (usually plain text and HTML).
        # Read only one version, so that words are not counted twice.
        alternatives = list(part.iter_parts())
        if alternatives:
            plain = [p for p in alternatives if p.get_content_type() == "text/plain"]
            yield from _text_parts(plain[0] if plain else alternatives[-1])
    elif part.is_multipart():
        for subpart in part.iter_parts():
            yield from _text_parts(subpart)
    elif part.get_content_maintype() == "text":
        yield _decode_text(part)


def _decode_text(part) -> str:
    """get_payload(decode=True) undoes base64 and quoted-printable encoding."""
    payload = part.get_payload(decode=True) or b""
    charset = part.get_content_charset() or "utf-8"
    try:
        text = payload.decode(charset, errors="replace")
    except LookupError:  # unknown charset name
        text = payload.decode("utf-8", errors="replace")
    if part.get_content_subtype() == "html":
        text = HTML_TAG_PATTERN.sub(" ", text)
    return text


def count_bad_words(text: str, bad_words: set[str]) -> int:
    """Count every occurrence of a bad word (case-insensitive, whole words only)."""
    return sum(1 for word in WORD_PATTERN.findall(text.lower()) if word in bad_words)


def domain_matches(domain: str | None, domains: set[str]) -> bool:
    """True if domain is listed, or is a subdomain of a listed domain."""
    if not domain:
        return False
    return any(domain == listed or domain.endswith("." + listed) for listed in domains)


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------

class SpamFilterAgent:
    """Simple reflex agent: classifies each email using only that email."""

    def __init__(self, allow_list: Iterable[str], restrict_list: Iterable[str],
                 bad_words: Iterable[str]):
        self.allow_list = {d.lower() for d in allow_list}
        self.restrict_list = {d.lower() for d in restrict_list}
        self.bad_words = {w.lower() for w in bad_words}

        # persistent: rules, a set of condition-action rules (in priority order)
        self.rules = [
            Rule("allow-list",
                 lambda s: domain_matches(s.sender_domain, self.allow_list),
                 MOVE_TO_EMAIL,
                 "sender domain {sender_domain} is on the allow list"),
            Rule("restrict-list",
                 lambda s: domain_matches(s.sender_domain, self.restrict_list),
                 MOVE_TO_SPAM,
                 "sender domain {sender_domain} is on the restrict list"),
            Rule("bad-words",
                 lambda s: s.bad_word_count > BAD_WORD_THRESHOLD,
                 MOVE_TO_SPAM,
                 "{bad_word_count} bad words found (more than %d)" % BAD_WORD_THRESHOLD),
            Rule("default",
                 lambda s: True,
                 MOVE_TO_EMAIL,
                 "{bad_word_count} bad words found (%d or fewer)" % BAD_WORD_THRESHOLD),
        ]

    @classmethod
    def from_files(cls, allow_path=DATA_DIR / "allow_list.txt",
                   restrict_path=DATA_DIR / "restrict_list.txt",
                   bad_words_path=DATA_DIR / "bad_words.txt") -> "SpamFilterAgent":
        return cls(load_list(allow_path), load_list(restrict_path), load_list(bad_words_path))

    def __call__(self, percept: bytes) -> str:
        """SIMPLE-REFLEX-AGENT(percept) returns an action."""
        return self.decide(percept).action

    def decide(self, percept: bytes) -> Decision:
        state = self.interpret_input(percept)
        rule = self.rule_match(state)
        action = rule.action
        return Decision(action, rule, state)

    def interpret_input(self, percept: bytes) -> EmailState:
        """INTERPRET-INPUT: turn the raw email into the state the rules look at."""
        message = BytesParser(policy=policy.default).parsebytes(percept)
        return EmailState(
            sender_domain=sender_domain(message),
            bad_word_count=count_bad_words(readable_text(message), self.bad_words),
        )

    def rule_match(self, state: EmailState) -> Rule:
        """RULE-MATCH: return the first rule whose condition matches the state."""
        for rule in self.rules:
            if rule.condition(state):
                return rule
        raise RuntimeError("no rule matched")  # unreachable: the default rule always matches
