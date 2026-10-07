"""Run the spam filter agent on a folder of .eml files.

Usage (from the project root):
    python -m q1_spam_filter.main <inbox_folder> [--output DIR] [--copy]

Example (demo on the test data, keeping the inbox intact):
    python -m q1_spam_filter.main q1_spam_filter/test_data/inbox --output output --copy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow "python q1_spam_filter/main.py ..." as well as "python -m q1_spam_filter.main ..."
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from q1_spam_filter.environment import MailboxEnvironment
from q1_spam_filter.spam_agent import MOVE_TO_SPAM, SpamFilterAgent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Classify .eml files as spam or not spam.")
    parser.add_argument("inbox", help="folder containing the .eml files to classify")
    parser.add_argument("--output", help="folder where spam/ and email/ are created "
                                         "(default: the inbox's parent folder)")
    parser.add_argument("--copy", action="store_true",
                        help="copy emails instead of moving them (keeps the inbox intact)")
    args = parser.parse_args(argv)

    if not Path(args.inbox).is_dir():
        print(f"Error: inbox folder not found: {args.inbox}", file=sys.stderr)
        return 1

    agent = SpamFilterAgent.from_files()  # lists from q1_spam_filter/data/
    environment = MailboxEnvironment(args.inbox, args.output, keep_originals=args.copy)
    results = environment.run(agent)

    if not results:
        print(f"No .eml files found in {args.inbox}")
        return 0

    width = max(len(r.filename) for r in results)
    for r in results:
        label = "SPAM " if r.action == MOVE_TO_SPAM else "EMAIL"
        print(f"{r.filename:<{width}}  ->  {label}  ({r.reason})")

    spam = sum(1 for r in results if r.action == MOVE_TO_SPAM)
    print(f"\n{len(results)} emails processed: {spam} spam, {len(results) - spam} not spam.")
    print(f"Results written to: {environment.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
