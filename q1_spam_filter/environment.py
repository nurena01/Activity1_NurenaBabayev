"""Q1 - Mailbox environment for the spam filter agent.

The environment supplies the percepts (the raw bytes of each .eml file in the
inbox) and carries out the agent's actions (the actuator): placing each file
in the spam/ or email/ directory.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from q1_spam_filter.spam_agent import MOVE_TO_EMAIL, MOVE_TO_SPAM

DESTINATIONS = {MOVE_TO_SPAM: "spam", MOVE_TO_EMAIL: "email"}


@dataclass(frozen=True)
class Result:
    filename: str
    action: str
    reason: str
    destination: Path


class MailboxEnvironment:
    """An inbox folder of .eml files plus the spam/ and email/ output folders.

    keep_originals=True copies the emails instead of moving them, so a demo
    inbox can be classified again and again.
    """

    def __init__(self, inbox_dir, output_dir=None, keep_originals=False):
        self.inbox_dir = Path(inbox_dir)
        self.output_dir = Path(output_dir) if output_dir else self.inbox_dir.parent
        self.keep_originals = keep_originals

    def emails(self) -> list[Path]:
        return sorted(p for p in self.inbox_dir.iterdir()
                      if p.is_file() and p.suffix.lower() == ".eml")

    def percept(self, path: Path) -> bytes:
        """Sensor: read the email exactly as stored on disk."""
        return path.read_bytes()

    def execute_action(self, path: Path, action: str) -> Path:
        """Actuator: place the email in the folder chosen by the agent."""
        folder = self.output_dir / DESTINATIONS[action]
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / path.name
        if destination.exists():
            destination.unlink()
        if self.keep_originals:
            shutil.copy2(path, destination)
        else:
            shutil.move(str(path), str(destination))
        return destination

    def run(self, agent) -> list[Result]:
        """Give each email to the agent as a percept and execute its action."""
        for folder in DESTINATIONS.values():
            (self.output_dir / folder).mkdir(parents=True, exist_ok=True)
        results = []
        for path in self.emails():
            decision = agent.decide(self.percept(path))
            destination = self.execute_action(path, decision.action)
            results.append(Result(path.name, decision.action, decision.reason, destination))
        return results
