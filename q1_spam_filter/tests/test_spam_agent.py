"""Tests for Q1 - spam filter email agent.

Run from the project root:
    python -m unittest discover -v
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from q1_spam_filter.environment import MailboxEnvironment
from q1_spam_filter.spam_agent import (
    MOVE_TO_EMAIL,
    MOVE_TO_SPAM,
    SpamFilterAgent,
    load_list,
)

INBOX = Path(__file__).resolve().parent.parent / "test_data" / "inbox"

# Expected classification of every file in test_data/inbox
EXPECTED = {
    "01_allow_list_with_bad_words.eml": MOVE_TO_EMAIL,
    "02_restrict_list_clean.eml": MOVE_TO_SPAM,
    "03_six_bad_words.eml": MOVE_TO_SPAM,
    "04_five_bad_words.eml": MOVE_TO_EMAIL,
    "05_base64_body.eml": MOVE_TO_SPAM,
    "06_text_attachment.eml": MOVE_TO_SPAM,
    "07_binary_attachment.eml": MOVE_TO_EMAIL,
    "08_mixed_case.eml": MOVE_TO_SPAM,
    "09_subdomain_allow.eml": MOVE_TO_EMAIL,
    "10_clean_unknown.eml": MOVE_TO_EMAIL,
    "11_quoted_printable.eml": MOVE_TO_SPAM,
    "12_html_body.eml": MOVE_TO_SPAM,
    "13_encrypted_body.eml": MOVE_TO_EMAIL,
    "14_plain_and_html_alternative.eml": MOVE_TO_EMAIL,
    "15_base64_text_attachment.eml": MOVE_TO_SPAM,
}


def make_email(sender, body, subject="test"):
    """Build a minimal plain-text .eml as bytes."""
    headers = f"To: me@example.com\nSubject: {subject}\n"
    if sender is not None:
        headers = f"From: {sender}\n" + headers
    return (headers + "\n" + body + "\n").encode("utf-8")


class TestSampleEmails(unittest.TestCase):
    """One test per sample email in test_data/inbox, using the real data/ lists."""

    @classmethod
    def setUpClass(cls):
        cls.agent = SpamFilterAgent.from_files()

    def decide(self, filename):
        return self.agent.decide((INBOX / filename).read_bytes())

    def check(self, filename, expected_action, expected_bad_words):
        decision = self.decide(filename)
        self.assertEqual(decision.action, expected_action, decision.reason)
        self.assertEqual(decision.state.bad_word_count, expected_bad_words)
        self.assertEqual(decision.action, EXPECTED[filename])

    def test_every_sample_file_has_an_expected_result(self):
        self.assertEqual(set(EXPECTED), {p.name for p in INBOX.glob("*.eml")})

    def test_01_allow_list_beats_bad_words(self):
        self.check("01_allow_list_with_bad_words.eml", MOVE_TO_EMAIL, 9)
        self.assertEqual(self.decide("01_allow_list_with_bad_words.eml").rule.name, "allow-list")

    def test_02_restrict_list_beats_clean_body(self):
        self.check("02_restrict_list_clean.eml", MOVE_TO_SPAM, 0)
        self.assertEqual(self.decide("02_restrict_list_clean.eml").rule.name, "restrict-list")

    def test_03_six_bad_words_is_spam(self):
        self.check("03_six_bad_words.eml", MOVE_TO_SPAM, 6)

    def test_04_exactly_five_bad_words_is_not_spam(self):
        self.check("04_five_bad_words.eml", MOVE_TO_EMAIL, 5)

    def test_05_base64_body_is_decoded(self):
        self.check("05_base64_body.eml", MOVE_TO_SPAM, 9)

    def test_06_text_attachment_is_read(self):
        self.check("06_text_attachment.eml", MOVE_TO_SPAM, 7)

    def test_07_binary_attachment_is_not_read(self):
        self.check("07_binary_attachment.eml", MOVE_TO_EMAIL, 0)

    def test_08_mixed_case_words_are_counted(self):
        self.check("08_mixed_case.eml", MOVE_TO_SPAM, 6)

    def test_09_subdomain_of_allowed_domain_is_allowed(self):
        self.check("09_subdomain_allow.eml", MOVE_TO_EMAIL, 8)

    def test_10_clean_email_from_unknown_domain(self):
        self.check("10_clean_unknown.eml", MOVE_TO_EMAIL, 0)

    def test_11_quoted_printable_body_is_decoded(self):
        self.check("11_quoted_printable.eml", MOVE_TO_SPAM, 6)

    def test_12_html_body_tags_are_ignored(self):
        self.check("12_html_body.eml", MOVE_TO_SPAM, 6)

    def test_13_encrypted_body_is_not_read(self):
        self.check("13_encrypted_body.eml", MOVE_TO_EMAIL, 0)

    def test_14_plain_and_html_versions_are_counted_once(self):
        # 4 bad words in each version; counting both would wrongly give 8 (spam)
        self.check("14_plain_and_html_alternative.eml", MOVE_TO_EMAIL, 4)

    def test_15_base64_text_attachment_is_read_and_spreadsheet_is_skipped(self):
        # Based on the EML format reference: a base64 text/plain attachment (readable)
        # and a base64 .xlsx attachment (application/..., not readable)
        decision = self.decide("15_base64_text_attachment.eml")
        self.check("15_base64_text_attachment.eml", MOVE_TO_SPAM, 6)
        self.assertEqual(decision.state.sender_domain, "bmw.eml.light.com")


class TestRules(unittest.TestCase):
    """Rule priority and edge cases, using small custom lists."""

    def setUp(self):
        self.agent = SpamFilterAgent(
            allow_list={"good.com", "both.com"},
            restrict_list={"bad.com", "both.com"},
            bad_words={"free", "cash", "prize"},
        )

    def test_allow_list_beats_bad_words(self):
        self.assertEqual(self.agent(make_email("a@good.com", "free " * 20)), MOVE_TO_EMAIL)

    def test_restrict_list_beats_clean_body(self):
        self.assertEqual(self.agent(make_email("a@bad.com", "hello")), MOVE_TO_SPAM)

    def test_domain_on_both_lists_uses_allow_list(self):
        self.assertEqual(self.agent(make_email("a@both.com", "hello")), MOVE_TO_EMAIL)

    def test_threshold_is_more_than_five(self):
        self.assertEqual(self.agent(make_email("a@x.com", "free cash prize free cash")), MOVE_TO_EMAIL)
        self.assertEqual(self.agent(make_email("a@x.com", "free cash prize free cash prize")), MOVE_TO_SPAM)

    def test_repeated_words_each_count(self):
        self.assertEqual(self.agent(make_email("a@x.com", "free " * 6)), MOVE_TO_SPAM)

    def test_only_whole_words_count(self):
        state = self.agent.interpret_input(make_email("a@x.com", "freedom carefree cashier prizes"))
        self.assertEqual(state.bad_word_count, 0)

    def test_punctuation_does_not_hide_words(self):
        state = self.agent.interpret_input(make_email("a@x.com", "FREE!!! cash, prize."))
        self.assertEqual(state.bad_word_count, 3)

    def test_html_only_alternative_is_used_when_there_is_no_plain_text(self):
        email = (b"From: a@x.com\nMIME-Version: 1.0\n"
                 b"Content-Type: multipart/alternative; boundary=B\n\n"
                 b"--B\nContent-Type: text/html\n\n<p>free free free free free free</p>\n--B--\n")
        self.assertEqual(self.agent(email), MOVE_TO_SPAM)

    def test_alternative_inside_mixed_plus_text_attachment(self):
        email = (b"From: a@x.com\nMIME-Version: 1.0\n"
                 b"Content-Type: multipart/mixed; boundary=M\n\n"
                 b"--M\nContent-Type: multipart/alternative; boundary=A\n\n"
                 b"--A\nContent-Type: text/plain\n\nfree cash prize\n"
                 b"--A\nContent-Type: text/html\n\n<p>free cash prize</p>\n--A--\n"
                 b"--M\nContent-Type: text/plain\nContent-Disposition: attachment; filename=a.txt\n\n"
                 b"free cash prize\n--M--\n")
        self.assertEqual(self.agent.interpret_input(email).bad_word_count, 6)

    def test_subject_is_not_part_of_the_body(self):
        email = make_email("a@x.com", "hello", subject="free free free free free free")
        self.assertEqual(self.agent(email), MOVE_TO_EMAIL)

    def test_subdomain_matches_but_lookalike_domains_do_not(self):
        self.assertEqual(self.agent(make_email("a@mail.good.com", "free " * 6)), MOVE_TO_EMAIL)
        self.assertEqual(self.agent(make_email("a@notgood.com", "free " * 6)), MOVE_TO_SPAM)
        self.assertEqual(self.agent(make_email("a@good.com.evil.net", "free " * 6)), MOVE_TO_SPAM)

    def test_domain_matching_is_case_insensitive(self):
        self.assertEqual(self.agent(make_email("A@BAD.COM", "hello")), MOVE_TO_SPAM)

    def test_display_name_is_ignored(self):
        state = self.agent.interpret_input(make_email('"good.com" <a@bad.com>', "hello"))
        self.assertEqual(state.sender_domain, "bad.com")

    def test_missing_from_header_falls_back_to_bad_words(self):
        self.assertEqual(self.agent.interpret_input(make_email(None, "hi")).sender_domain, None)
        self.assertEqual(self.agent(make_email(None, "hello")), MOVE_TO_EMAIL)
        self.assertEqual(self.agent(make_email(None, "free " * 6)), MOVE_TO_SPAM)

    def test_agent_has_no_memory(self):
        """A simple reflex agent's answer depends only on the current percept."""
        spam = make_email("a@x.com", "free " * 6)
        clean = make_email("a@x.com", "hello")
        first = [self.agent(spam), self.agent(clean)]
        second = [self.agent(clean), self.agent(spam)]
        self.assertEqual(first, [MOVE_TO_SPAM, MOVE_TO_EMAIL])
        self.assertEqual(second, [MOVE_TO_EMAIL, MOVE_TO_SPAM])


class TestLoadList(unittest.TestCase):
    def test_ignores_comments_and_blank_lines_and_lowercases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "list.txt"
            path.write_text("# comment\n\nFree\n  CASH  # trailing comment\n", encoding="utf-8")
            self.assertEqual(load_list(path), {"free", "cash"})


class TestMailboxEnvironment(unittest.TestCase):
    """The actuator places each email in spam/ or email/."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.inbox = self.tmp / "inbox"
        shutil.copytree(INBOX, self.inbox)
        self.agent = SpamFilterAgent.from_files()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def folder_contents(self, name):
        return {p.name for p in (self.tmp / name).glob("*.eml")}

    def test_emails_are_moved_to_the_correct_folders(self):
        results = MailboxEnvironment(self.inbox).run(self.agent)

        self.assertEqual(len(results), len(EXPECTED))
        self.assertEqual(self.folder_contents("spam"),
                         {f for f, a in EXPECTED.items() if a == MOVE_TO_SPAM})
        self.assertEqual(self.folder_contents("email"),
                         {f for f, a in EXPECTED.items() if a == MOVE_TO_EMAIL})
        self.assertEqual(list(self.inbox.glob("*.eml")), [])

    def test_copy_mode_keeps_the_inbox(self):
        MailboxEnvironment(self.inbox, keep_originals=True).run(self.agent)
        self.assertEqual(len(list(self.inbox.glob("*.eml"))), len(EXPECTED))
        self.assertEqual(len(self.folder_contents("spam")) + len(self.folder_contents("email")),
                         len(EXPECTED))

    def test_both_folders_exist_even_when_empty(self):
        for f in self.inbox.glob("*.eml"):
            if f.name != "10_clean_unknown.eml":
                f.unlink()
        MailboxEnvironment(self.inbox).run(self.agent)
        self.assertTrue((self.tmp / "spam").is_dir())
        self.assertEqual(self.folder_contents("email"), {"10_clean_unknown.eml"})

    def test_running_twice_with_copy_does_not_fail(self):
        env = MailboxEnvironment(self.inbox, keep_originals=True)
        env.run(self.agent)
        env.run(self.agent)
        self.assertEqual(len(self.folder_contents("spam")) + len(self.folder_contents("email")),
                         len(EXPECTED))


if __name__ == "__main__":
    unittest.main()
