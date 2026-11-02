# reask benchmark

> **v2 is preregistered in [`v2/`](v2/PREREGISTRATION.md) and replaces this suite once it has
> run.** v1 below compares reask with the question as first asked, on short fresh sessions; v2
> measures what reask is for: whether one re-ask lets someone who lost the context decide
> everything, correctly, without asking again, and in how many words. Until then the v1 cases
> stay as they are and serve v2 as grader controls.

reask is for the moment you cannot answer your agent's question. You have three ways out:

1. **Answer anyway**, without really understanding the choice.
2. **Ask by hand**: "I didn't quite get that, ask again in plain words".
3. **Use reask.** Type `/reask`, or ask in your own words with reask installed; the skill loads
   either way.

This suite compares the three on the same six moments, using Claude Code's plugin eval harness,
`claude plugin eval`. The harness runs every case with the plugin and without it. How often reask
finds a better option in real work is counted separately, in [`field/`](field).

## How a case works

1. **A real pending question.** An agent with no skills was given a task in a small fixture
   project (`project/`) and told to stop and ask before deciding. Its question is real Claude Opus
   5.5 output, recorded once and replayed from `history.jsonl`. It was not written for the
   benchmark. The transcript is reduced to the dialogue, with local paths replaced by `/work`.
2. **The user's reply** is a hand-written re-ask, the same in both arms: "I didn't quite get that.
   Can you ask again in plain words?", in Russian for the Russian case. Without the plugin, this
   is option 2 above. With it, the same words load reask on its own, which is option 3. Nobody
   types `/reask`, because a command that does not exist in one arm would rig the comparison.
3. **The graders** read only the agent's final message, one criterion each. The original question
   is graded with the same rubrics too, as option 1 (`grade_original.py`).

| Case | The pending question | What it stresses |
|---|---|---|
| `pricing-cache` | What a price cache is keyed on, when some products are priced per country | a trade-off with a concrete wrong-price risk |
| `orders-migration` | Three questions about adding a required column to a 40M-row table | several open questions at once |
| `reliability-plan` | Which tickets fit a 10-day sprint, all referred to by code (PLAT-412, ADR-7, RFC-3) | references the user has to look up |
| `ci-setup` | Six CI questions; the user answers two and bounces four | keeping the answers already given |
| `token-storage-ru` | Where a web app keeps its login token; the user writes in Russian | answering in the user's language |
| `dead-code` | Delete one unused file, yes or no | an easy call that should stay short |

| Grader | Passes when |
|---|---|
| cold reader | someone who never saw the session can state the decision, the options with their costs, and the project fact that makes it matter (facts written by hand per case) |
| pros and cons | every option, the recommended one included, has a downside stated |
| grounded recommendation | the recommendation cites a fact from the project, not generic advice |
| answerable ending | the message ends by asking for the open decisions, each answerable in a word |
| new option | the message proposes a concrete option the original question did not list (the list is written by hand per case) |
| codes explained, user's language, keeps answers, stays short | per case, as named; "short" means 200 words, against the skill's own "about 150" |
| skill fired | an indicator only, not scored: the reask skill loaded |

## Results, 2026-11-02

Claude Code 2.1.312. The agent is `claude-opus-5-5` and the judge is `claude-sonnet-5-5`, with
three votes per verdict and the majority winning. There are 3 runs per arm and 36 runs in all,
costing $8.55. Every reply is in [`results/2026-11-02/replies/`](results/2026-11-02/replies), the
per-run verdicts are in [`summary.json`](results/2026-11-02/summary.json), and the original
questions' verdicts are in [`original-question.json`](results/2026-11-02/original-question.json).

| Grader | 1. Answer anyway (the question as asked) | 2. "Ask again in plain words" | 3. reask |
|---|---|---|---|
| cold reader | 0/6 | 7/18 | **17/18** |
| pros and cons | 0/6 | 5/18 | **16/18** |
| grounded recommendation | 4/6 | 15/18 | **18/18** |
| answerable ending | 1/6 | 7/18 | **10/18** |
| new option | – | 0/18 | **4/18** |
| codes explained | 0/1 | 3/3 | 3/3 |
| user's language | 1/1 | 3/3 | 3/3 |
| keeps answers | – | 3/3 | 3/3 |
| stays short | 1/1 | **3/3** | 0/3 |
| skill fired (not scored) | – | – | 18/18 |

| Case | "Ask again" | reask | Words (median) | Cost per reply |
|---|---|---|---|---|
| ci-setup | 0.56 | 0.67 | 302 → 1068 | $0.20 → $0.46 |
| dead-code | 0.50 | 0.83 | 86 → 292 | $0.13 → $0.20 |
| orders-migration | 0.20 | 0.73 | 232 → 824 | $0.20 → $0.26 |
| pricing-cache | 0.53 | 0.80 | 212 → 444 | $0.15 → $0.22 |
| reliability-plan | 0.33 | 0.61 | 255 → 651 | $0.27 → $0.34 |
| token-storage-ru | 0.56 | 0.72 | 169 → 451 | $0.19 → $0.24 |
| **all** | **0.45** | **0.73** | 207 → 567 | $0.19 → $0.28 |

**What a plain re-ask does.** Asked for plain words, the agent shortens its question and drops
facts: someone who never saw the session could follow it in 7 of 18 runs. The downsides of the
options mostly go, too (5 of 18).

**What reask does instead.** The re-ask could be followed cold in 17 of 18 runs, and gave every
option's downside, the recommended one's included, in 16 of 18.

**New options.** Of the 4 new options in the benchmark, 3 are trivial: "leave the file as it is"
in `dead-code`. The fourth is the real thing. In `orders-migration`, reask remembered that Postgres
adds a column with a fixed default instantly, proposed adding `region` as NOT NULL with default
`UNKNOWN`, and replaced its own earlier recommendation with it. The README shows that run. The
fixture projects are small and leave little room for a better option. In the author's real
sessions a new option came up in 63% of re-asks ([`field/`](field)).

**What it costs.** A re-ask is about 2.7 times longer than a plain one. It takes about 4 turns
instead of 1: the skill loads, then the agent looks at the project before it recommends, as
SKILL.md asks. It costs about 9 cents more per reply with Opus 5.5.

**Where it falls short.** Two weak spots are open:

- **Easy calls run long.** The `dead-code` yes/no comes back at about 290 words. SKILL.md promises
  about 150 for a firm call on familiar ground.
- **Several bounced questions spread their asks.** Each question gets its own block ending in its
  own question, so in a reply of 800 to 1,000 words the asks end up in the middle. The answerable
  ending passed where the reply closed with a recap of every ask, as in the `orders-migration`
  run the README shows.

**Limits of this benchmark.** Six cases and three runs per arm are a small sample. The judge is
one model. The fixture projects were written for the benchmark, though the questions in them are
real agent output. Read the replies before you trust the numbers.

## Run it yourself

From the repository root. The first command costs about $9 with these models, and the second,
which grades only six messages, costs far less:

```bash
claude plugin eval . --model claude-opus-5-5 --judge-model claude-sonnet-5-5 --no-publish --threshold 0 -j 4
python3 evals/grade_original.py evals original-question.json
```

`--case pricing-cache` runs one case, and `--runs 1` runs one pass per arm. The harness writes its
results to `evals/results/<timestamp>/`.
