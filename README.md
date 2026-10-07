# DPS970 – Activity 1

| | |
|---|---|
| **Student** | Nurena Babayev |
| **Student ID** | 159544238 |
| **Email** | nbabayev1@myseneca.ca |
| **Professor** | Davoud Gholamiangonabadi |
| **Course** | DPS970 – Activity 1 |
| **GitHub repository** | https://github.com/nurena01/Activity1_NurenaBabayev |
| **Language** | Python 3.10+ (standard library only, so nothing needs to be installed) |

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
- The allow list, restrict list and bad-word list are read from [`q1_spam_filter/data/`](q1_spam_filter/data/).

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

**Why this agent acts rationally.** In Chapter 2, a rational agent chooses the action that maximizes the expected value of its performance measure, given the percept sequence to date. Here the performance measure is classifying every email correctly according to the allow list, restrict list and bad-word rule. For each percept (email), the rules above select exactly the action that the performance measure rewards, so no other action could score better. The agent is not omniscient: it cannot read encrypted or binary parts, so it decides using the information it *can* perceive, which is what rationality requires.

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

## How to run

```
python -m q2_water_jugs.main
```

This solves the assignment's puzzle (jugs of 12, 8 and 3 gallons, measure 1 gallon) and prints:

```
Jugs: 12, 8, 3 gallons | goal: exactly 1 gallon(s) in any jug
Initial state: (0, 0, 0) | reachable states: 314

Step 0: (0, 0, 0)  (start)
Step 1: (12, 0, 0)  <- Fill 12
Step 2: (4, 8, 0)  <- Pour 12->8
Step 3: (1, 8, 3)  <- Pour 12->3

Solved in 3 steps (path cost 3).
```

(`python q2_water_jugs/main.py` works as well.)

## Files

| File | Purpose |
|---|---|
| [`problem.py`](q2_water_jugs/problem.py) | Problem formulation: states, `actions`, `result` (transition model), `is_goal`, `action_cost` |
| [`search.py`](q2_water_jugs/search.py) | `Node`, `expand` (Figure 3.7), `breadth_first_search` (Figure 3.9), and a tree-search DFS used to support answer c) |
| [`main.py`](q2_water_jugs/main.py) | Command-line program that prints the solution |
| [`test_data/puzzles.json`](q2_water_jugs/test_data/puzzles.json) | 9 test puzzles with their known shortest solution lengths (7 solvable, 2 unsolvable) |
| [`tests/test_water_jugs.py`](q2_water_jugs/tests/test_water_jugs.py) | 25 unit tests |

## a) States, actions and transition model

**States.** A state is a tuple **`(a, b, c)`**, where `a`, `b` and `c` are the gallons currently in the 12-, 8- and 3-gallon jugs. All amounts are whole numbers, because every action fills or empties a jug completely, or pours until one jug is empty or the other is full. The limits are 0 ≤ a ≤ 12, 0 ≤ b ≤ 8 and 0 ≤ c ≤ 3, so there are 13 × 9 × 4 = 468 possible tuples. Only **314** of them can actually be reached from the initial state.

**Initial state.** **`(0, 0, 0)`**: all three jugs are empty.

**Goal states.** Any state where **some jug holds exactly 1 gallon**: `a = 1` or `b = 1` or `c = 1`. Examples are `(1, 8, 3)`, `(0, 1, 0)` and `(4, 0, 1)`.

**Actions.** There are 12 actions in total. Here *i* and *j* are jugs, and *cap(i)* is the capacity of jug *i*.

| Action | Applicable when | Count |
|---|---|---|
| `Fill(i)`: fill jug *i* from the faucet | jug *i* is not full | 3 |
| `Empty(i)`: pour jug *i* onto the ground | jug *i* is not empty | 3 |
| `Pour(i, j)`: pour jug *i* into jug *j* | *i* ≠ *j*, jug *i* is not empty and jug *j* is not full | 6 |

Actions that would not change the state are not applicable, for example filling a jug that is already full.

**Transition model `RESULT(s, action)`.**
- `Fill(i)`: jug *i* becomes *cap(i)*. The other jugs are unchanged.
- `Empty(i)`: jug *i* becomes 0. The other jugs are unchanged.
- `Pour(i, j)`: the amount moved is **`m = min(amount in i, cap(j) − amount in j)`**. Jug *i* loses *m* and jug *j* gains *m*, so pouring stops when *i* is empty or *j* is full.

**Action cost.** Each action costs 1, so the path cost is the number of steps.

*Example:* `RESULT((12, 0, 0), Pour(12→8)) = (4, 8, 0)`, because m = min(12, 8 − 0) = 8.

## b) Does a heuristic function make sense?

**A heuristic can be defined, but it is of limited value for this problem.**

A possible heuristic, described informally:

- **h = 0** if some jug already holds 1 gallon (a goal state).
- **h = 1** if one single action would produce 1 gallon in some jug. For example, in `(4, 8, 0)`, `Pour 12→3` leaves 1 gallon in the 12-gallon jug.
- **h = 2** otherwise.

This heuristic is **admissible**: it never overestimates, because a state that is not a goal and cannot reach a goal in one action needs at least 2 more actions. It is also **consistent**, because h can drop by at most 1 per action, and each action costs 1. It could therefore be used with A\* or greedy best-first search. It is implemented as `WaterJugProblem.heuristic()`, and the tests check that it is admissible and consistent in all 314 reachable states.

**Why it does not help much:**
- **The state space is tiny.** There are only 314 reachable states, so uninformed BFS finds the optimal solution instantly. A heuristic cannot save meaningful work.
- **"Closeness" is misleading here.** A natural idea would be "how many gallons the closest jug is away from 1". However, the number of gallons says little about how many actions remain, because one pour can move up to 8 gallons at once. In `(5, 4, 3)` the closest jug is 2 gallons away, yet one action (`Pour 12→8`) gives `(1, 8, 3)`. This distance **overestimates** the real cost in 22 of the 314 reachable states, so it is **not admissible**, and A\* could return a non-optimal solution with it.
- **The best admissible heuristics are weak.** Any heuristic that never overestimates can only distinguish "0 steps", "1 step" and "2 or more steps", which is very little guidance.

## c) Is any search algorithm guaranteed to reach a goal state?

**No, not every search algorithm is guaranteed to reach a goal. But complete algorithms such as breadth-first search are guaranteed to, for this problem.**

1. **A goal is reachable.** A solution exists: Fill 12 → Pour 12→8 → Pour 12→3 gives `(1, 8, 3)`. Our BFS finds it, so at least one goal state can be reached from the initial state.
2. **The state space is finite.** There are at most 468 states (314 reachable), and every state has at most 12 actions.
3. **Complete algorithms will find the goal.** BFS, uniform-cost search, iterative deepening and graph-search DFS (DFS with a reached set) are guaranteed to find a solution when one exists in a finite state space with a finite branching factor. Graph-search versions never expand the same state twice, so they terminate after at most 314 states.
4. **BFS is also optimal here.** All actions cost 1, and BFS finds the shallowest goal, so its 3-step solution is the shortest possible.
5. **Incomplete algorithms may never reach it.** The state space contains **cycles**: you can always undo an action, for example Fill then Empty. **Depth-first tree search** (which keeps no record of visited states) can loop forever. Our test `test_tree_search_dfs_loops_forever` shows this. DFS tries `Fill 12`, `Fill 8`, `Fill 3`, and then cycles forever between `(0, 8, 3)` and `(12, 8, 3)` by repeating `Empty 12`, `Fill 12`. It never reaches the goal, even after 10,000 expansions. Greedy best-first tree search without repeated-state checking can loop in the same way.

**In summary:** completeness depends on the algorithm. In this finite state space, any complete algorithm (especially a graph search that tracks reached states) is guaranteed to reach a goal, but tree-search DFS is not.

## d) Implementation: breadth-first search (Figure 3.9)

[`search.py`](q2_water_jugs/search.py) follows the textbook's pseudocode line by line:

```
function BREADTH-FIRST-SEARCH(problem) returns a solution node or failure
    node <- NODE(problem.INITIAL)
    if problem.IS-GOAL(node.STATE) then return node
    frontier <- a FIFO queue, with node as an element
    reached <- {problem.INITIAL}
    while not IS-EMPTY(frontier) do
        node <- POP(frontier)
        for each child in EXPAND(problem, node) do
            s <- child.STATE
            if problem.IS-GOAL(s) then return child
            if s is not in reached then
                add s to reached
                add child to frontier
    return failure
```

| Pseudocode | Python |
|---|---|
| `NODE` (state, parent, action, path cost) | `Node` class, with `path()` and `solution()` |
| `EXPAND(problem, node)` (Figure 3.7) | `expand(problem, node)`, a generator that yields child nodes |
| FIFO queue `frontier` | `collections.deque`: `append()` adds to the back, `popleft()` takes from the front |
| `reached` | a Python `set` of states |
| `problem.INITIAL`, `ACTIONS`, `RESULT`, `IS-GOAL`, `ACTION-COST` | `WaterJugProblem.initial`, `actions()`, `result()`, `is_goal()`, `action_cost()` |
| `failure` | `FAILURE` (`None`) |

**Early goal test.** As in Figure 3.9, each child is tested as soon as it is *generated*, not when it is later popped from the frontier. This is safe for BFS, because the first goal generated is always at the shallowest depth, and it saves expanding a whole extra level of the tree.

### Test data and tests

[`test_data/puzzles.json`](q2_water_jugs/test_data/puzzles.json) contains 9 puzzles:

| Puzzle | Expected result |
|---|---|
| **12, 8, 3 → 1 (the assignment)** | **3 steps** |
| 12, 8, 3 → 5 | 2 steps |
| 12, 8, 3 → 7 | 4 steps |
| 12, 8, 3 → 0 (initial state is already a goal) | 0 steps |
| 5, 3 → 4 | 6 steps |
| 4, 3 → 2 | 4 steps |
| 8, 5, 3 → 4 | 6 steps |
| 4, 6 → 1 (impossible: every amount is even) | failure |
| 12, 8, 3 → 13 (larger than any jug) | failure |

The tests check:
- **Transition model:** every action type (fill, empty, partial pour, full pour).
- **State validity:** across all 314 reachable states, no action overflows a jug, goes below 0, or creates or loses water when pouring.
- **Search structure:** `Node`, `expand`, `path()` and `solution()`.
- **Every test puzzle:**
  - BFS returns a solution;
  - replaying that solution from the initial state really reaches a goal;
  - its length equals the known shortest length;
  - an independent layer-by-layer check confirms that no shorter solution exists.
- **Unsolvable puzzles:** they return failure.
- **Answer c):** tree-search DFS loops forever, while BFS succeeds.
