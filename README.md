# DPS970 – Activity 1

**Student:** Nurena Babayev
**Language:** Python 3.10+ (standard library only, so nothing needs to be installed)

| Question | Folder |
|---|---|
| Q1 – Spam Filter Email Agent | [`q1_spam_filter/`](q1_spam_filter/) |
| Q2 – Water Jug Search Problem | [`q2_water_jugs/`](q2_water_jugs/) |

---

## How to run the tests

From the project root folder:

```
python -m unittest discover -v
```

This finds and runs every test in the project. The tests also run automatically
on GitHub on every push, using GitHub Actions ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)).

---

# Q1 – Spam Filter Email Agent

## How to run

```
python -m q1_spam_filter.main q1_spam_filter/test_data/inbox --output output --copy
```

(`python q1_spam_filter/main.py q1_spam_filter/test_data/inbox --output output --copy` works too.)

- `inbox`: the folder of `.eml` files to classify.
- `--output`: the folder where `spam/` and `email/` are created. The default is the inbox's parent folder.
- `--copy`: copy the emails instead of moving them, so the demo inbox stays intact. Leave it out to **move** the emails, as the assignment describes.
- `--allow`, `--restrict`, `--bad-words`: use different list files. The defaults are in [`q1_spam_filter/data/`](q1_spam_filter/data/).

Each email is printed with the agent's decision and the reason, for example:

```
03_six_bad_words.eml   ->  SPAM   (6 bad words found (more than 5))
```

## Files

| File | Purpose |
|---|---|
| [`spam_agent.py`](q1_spam_filter/spam_agent.py) | The simple reflex agent: INTERPRET-INPUT, RULE-MATCH, condition-action rules |
| [`environment.py`](q1_spam_filter/environment.py) | The mailbox environment: gives percepts and executes actions (moves files) |
| [`main.py`](q1_spam_filter/main.py) | Command-line program |
| [`data/`](q1_spam_filter/data/) | `allow_list.txt`, `restrict_list.txt`, `bad_words.txt` |
| [`test_data/inbox/`](q1_spam_filter/test_data/inbox/) | 15 sample `.eml` files, one per test case |
| [`tests/test_spam_agent.py`](q1_spam_filter/tests/test_spam_agent.py) | 36 unit tests |

## a) PEAS description

| | |
|---|---|
| **Performance measure** | Emails are classified correctly: spam ends up in `spam/` and legitimate email in `email/`. The allow-list and restrict-list rules are always followed. The agent minimizes false positives (real email sent to spam) and false negatives (spam left in the inbox). Every email in the inbox is processed. |
| **Environment** | The inbox folder of `.eml` files (headers plus a body that may be plain text, base64, quoted-printable, HTML, multipart, with text or binary attachments, or encrypted). Also the allow list, restrict list and bad-word list, and the `spam/` and `email/` output directories. |
| **Actuators** | File-system operations that place (move) each email file into the `spam/` directory or the `email/` directory. |
| **Sensors** | Reading the `.eml` file. The email parser reads the `From:` header to get the sender's domain, decodes the body and text attachments (base64 / quoted-printable / HTML), and splits the text into words to count bad words. |

## b) Properties of the task environment

| Property | Classification | Reason |
|---|---|---|
| Observable | **Partially observable** | The headers are plain text, but parts of the body may be encrypted or in a format the agent cannot read (binary attachments). The agent cannot see the sender's true intent. |
| Agents | **Single-agent** | Only the filter makes decisions during classification. (Spammers are adversaries who write emails to avoid filters, but they do not act while the agent is deciding.) |
| Deterministic / stochastic | **Deterministic** | The same email with the same lists always produces the same action, and moving a file always has the expected result. |
| Episodic / sequential | **Episodic** | Each email is one independent episode. Classifying one email does not affect how the next one is classified. |
| Static / dynamic | **Static** | The email and the lists do not change while the agent is deciding. |
| Discrete / continuous | **Discrete** | There is a finite number of emails, a countable number of words, and only two possible actions. |
| Known / unknown | **Known** | The rules for what makes an email spam are given in full by the lists and the bad-word threshold. |

## c) Most appropriate agent type: simple reflex agent

A **simple reflex agent** is the most appropriate choice:

- **The decision depends only on the current percept.** Everything needed to classify an email is inside that email (the sender's domain and the body) plus the fixed lists. Since the environment is **episodic**, previous emails tell the agent nothing about the current one, so **internal state (memory)** is not needed. A model-based agent would add complexity without improving the decision.
- **The rules are condition-action rules.** The assignment specifies the behaviour directly as *if-then* rules ("if the domain is on the allow list then not spam ..."). This is exactly the structure of a simple reflex agent.
- **No goals or utilities to compare.** There is no sequence of actions to plan (so no goal-based search), and there are only two actions with a fixed rule for choosing between them (so no utility trade-off).
- **Partial observability is not a problem here.** A simple reflex agent works best when the environment is fully observable. Our environment is partially observable only because some content is unreadable, and the rules are defined in terms of what *can* be read. Remembering past emails would not reveal the hidden content, so memory still would not help.

*Possible extension:* a **learning agent** could learn new bad words or domains from user feedback (a critic marking mistakes). The assignment gives fixed lists, so learning is not required.

## d) Implementation

The agent in [`spam_agent.py`](q1_spam_filter/spam_agent.py) follows the textbook's **SIMPLE-REFLEX-AGENT** pseudocode:

```
function SIMPLE-REFLEX-AGENT(percept) returns an action
    persistent: rules, a set of condition-action rules
    state  <- INTERPRET-INPUT(percept)
    rule   <- RULE-MATCH(state, rules)
    action <- rule.ACTION
    return action
```

| Pseudocode | Python |
|---|---|
| `percept` | raw bytes of one `.eml` file |
| `INTERPRET-INPUT` | `SpamFilterAgent.interpret_input()` returns `EmailState(sender_domain, bad_word_count)` |
| `rules` | `SpamFilterAgent.rules`, a list of `Rule(condition, action)` in priority order |
| `RULE-MATCH` | `SpamFilterAgent.rule_match()` returns the first rule whose condition is true |
| `rule.ACTION` | `MoveToEmail` or `MoveToSpam` |

**Condition-action rules (checked in this order, first match wins):**

1. Sender's domain is on the **allow list** → `MoveToEmail` (regardless of contents)
2. Sender's domain is on the **restrict list** → `MoveToSpam` (regardless of contents)
3. **More than 5** bad words in the body → `MoveToSpam`
4. Otherwise → `MoveToEmail`

The **environment** ([`environment.py`](q1_spam_filter/environment.py)) gives each email to the agent as a percept and then carries out the action by placing the file in `spam/` or `email/`.

### Assumptions

The assignment leaves some details open, so these are the decisions made:

- The restrict list contains **unsafe** domains (the assignment text says "safe domains", which appears to be a typo, since those emails are classified as spam).
- If a domain is on **both** lists, the **allow list wins**, because allow-listed email is "non-spam regardless of its contents".
- **Subdomains** match: `mail.seneca.ca` matches `seneca.ca`. Lookalike domains such as `notseneca.ca` do **not** match.
- "More than 5 words" means **6 or more occurrences**. A word that appears 3 times counts 3 times.
- Bad words are matched **case-insensitively** as **whole words**: `FREE!` counts, `freedom` does not.
- Only the **body** is searched (including `text/*` attachments), not the Subject header, as the assignment says "within the body".
- Encoded bodies (base64, quoted-printable) are decoded. HTML tags are removed before counting.
- When an email contains the same text in several formats (`multipart/alternative`, usually plain text + HTML), only **one** version is read (plain text preferred), so words are not counted twice.
- Non-text parts (binary attachments, encrypted content) cannot be read and are skipped.
- Bad words are single words (one per line in `bad_words.txt`).
- An email with a missing or invalid `From:` address is treated as coming from an unknown domain, so only the bad-word rule applies.

### Test data

| File | What it tests | Expected |
|---|---|---|
| `01_allow_list_with_bad_words.eml` | Allowed domain with 9 bad words | email |
| `02_restrict_list_clean.eml` | Restricted domain with a clean body | spam |
| `03_six_bad_words.eml` | Exactly 6 bad words | spam |
| `04_five_bad_words.eml` | Exactly 5 bad words (boundary) | email |
| `05_base64_body.eml` | Base64-encoded body | spam |
| `06_text_attachment.eml` | Bad words only in a text attachment | spam |
| `07_binary_attachment.eml` | Bad words only in a binary attachment (unreadable) | email |
| `08_mixed_case.eml` | `FREE Free fReE ...` | spam |
| `09_subdomain_allow.eml` | Subdomain of an allowed domain | email |
| `10_clean_unknown.eml` | Normal email from an unknown domain | email |
| `11_quoted_printable.eml` | Quoted-printable body with words split across lines | spam |
| `12_html_body.eml` | HTML body with tags around the words | spam |
| `13_encrypted_body.eml` | PGP-encrypted body (unreadable) | email |
| `14_plain_and_html_alternative.eml` | Same text as plain and HTML, 4 bad words: must be counted **once** | email |
| `15_base64_text_attachment.eml` | Based on the EML format reference: base64 `text/plain` attachment (read) + `.xlsx` attachment (skipped) | spam |

The tests also check:
- the rule priority;
- a domain on both lists;
- whole-word matching;
- that the Subject header is ignored;
- lookalike domains;
- a missing `From:` header;
- that the agent has no memory;
- that the files really end up in the correct folder.

---

# Q2 – Water Jug Search Problem

*Coming next.*
