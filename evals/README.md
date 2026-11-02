# reask benchmark

Does reask make a re-asked question easier to answer than the agent's own re-ask? This suite
measures that with Claude Code's plugin eval harness, `claude plugin eval`, which runs every case
twice: once with the plugin loaded and once without it.

## How a case works

Each case is a moment where an agent is waiting on you:

1. **A real opening turn.** An agent with no skills was given a task in a small fixture project
   (`project/`) and told to stop and ask before deciding. Its question is real Claude Opus 5.5
   output, recorded once and replayed from `history.jsonl`. It was not written for the benchmark.
   The transcript is reduced to the dialogue, with local paths replaced by `/work`.
2. **The user's reply.** Both arms get the same plain-language message, such as "Sorry, I stepped
   away and lost the thread. I don't understand what you're asking me. Ask it again." Nobody types
   `/reask`, because a command that does not exist in the no-plugin arm would rig the result. The
   skill has to load on its own.
3. **The graders** read only the agent's final message. Each one is a single criterion, so the
   table below shows where the difference comes from.

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
| cold reader | someone who never saw the session can state the decision, the options with their costs, and the project fact that makes it matter (facts written by hand per case in `graders/cold-reader.md`) |
| pros and cons | every option, the recommended one included, has a downside stated |
| grounded recommendation | the recommendation cites a fact from the project, not generic advice |
| answerable ending | the message ends by asking for the open decisions, each answerable in a word |
| codes explained, user's language, keeps answers, stays short | per case, as named; "short" is 200 words, against the skill's own "about 150" |
| skill fired | an indicator only, not scored: the reask skill loaded |

## Results, 2026-11-02

Claude Code 2.1.312. The agent is `claude-opus-5-5` and the judge is `claude-sonnet-5-5` (three
votes per verdict, majority wins). There are 3 runs per arm and 36 runs in all, costing $7.79.
Every reply is in [`results/2026-11-02/replies/`](results/2026-11-02/replies), and the per-run
grader verdicts are in [`summary.json`](results/2026-11-02/summary.json).

| Grader | Without reask | With reask |
|---|---|---|
| cold reader | 10/18 | **18/18** |
| pros and cons | 6/18 | **13/18** |
| grounded recommendation | 16/18 | **18/18** |
| answerable ending | 7/18 | **10/18** |
| codes explained | 3/3 | 3/3 |
| user's language | 3/3 | 3/3 |
| keeps answers | 3/3 | 3/3 |
| stays short | **3/3** | 0/3 |
| skill fired (not scored) | – | 18/18 |

| Case | Without | With | Words (median) | Cost per reply |
|---|---|---|---|---|
| ci-setup | 0.67 | 0.67 | 391 → 1106 | $0.18 → $0.42 |
| dead-code | 0.47 | 0.80 | 76 → 336 | $0.09 → $0.19 |
| orders-migration | 0.25 | 0.75 | 271 → 956 | $0.18 → $0.28 |
| pricing-cache | 0.83 | 0.92 | 210 → 487 | $0.14 → $0.18 |
| reliability-plan | 0.60 | 0.87 | 275 → 602 | $0.20 → $0.32 |
| token-storage-ru | 0.80 | 0.87 | 150 → 499 | $0.18 → $0.24 |
| **all** | **0.60** | **0.81** | 238 → 548 | $0.16 → $0.27 |

**What reask buys.** Without it, the agent's re-ask could be followed cold in 10 of 18 runs; with
it, in all 18. The re-ask also states the downside of every option far more often (6 → 13 of 18),
most of all the downside of the option the agent recommends.

**What it costs.** A re-ask is about 2.3 times longer, takes 3 to 5 turns instead of 1 (the skill
loads, then the agent looks at the project before it recommends, as SKILL.md asks), and costs about 11 cents more per reply
with Opus 5.5.

**Where it falls short.** Two weak spots are open:

- **Easy calls run long.** The `dead-code` yes/no comes back at about 330 words. SKILL.md promises
  about 150 for a firm call on familiar ground.
- **Several bounced questions spread their asks.** Each question gets its own block ending in its
  own question. In a reply of 1,000 words, the asks end up in the middle, and the judge marks the
  ending as unanswerable (`orders-migration`, `ci-setup`). In `ci-setup` this cancels the gains,
  and the score is level.

**Limits of this benchmark.** Six cases and three runs per arm are a small sample. The judge is
one model. The fixture projects were written for the benchmark, though the questions in them are
real agent output. Read the replies before you trust the numbers.

## Run it yourself

From the repository root (it costs about $8 with these models):

```bash
claude plugin eval . --model claude-opus-5-5 --judge-model claude-sonnet-5-5 --no-publish --threshold 0 -j 4
```

`--case pricing-cache` runs one case. `--runs 1` runs one pass per arm. Results go to
`evals/results/<timestamp>/`.
