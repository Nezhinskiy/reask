# reask benchmark v2: results, 2026-11-02

What was asked: after one re-ask, can someone who lost the context make every open decision,
correctly, without asking again, and in how many words? Design, hypotheses and the analysis plan
are in [`PREREGISTRATION.md`](PREREGISTRATION.md); deviations from it are listed at the end of
this page, and every one of them is reported, not hidden.

Claude Code 2.1.312. Agent `claude-opus-5-5`, judge `claude-sonnet-5-5` with three votes per
verdict. Nine scenarios (seven development, two held out), four cells, 3 runs each: 108 main runs
for $65.93, plus 54 trigger runs for $17.03. Every reply is in
[`results/2026-11-02/replies/`](results/2026-11-02/replies), one file per scenario and cell, with
each run's verdicts above it; per-run data is in
[`summary.json`](results/2026-11-02/summary.json).

| Cell | What the user types after the question | Plugin |
|---|---|---|
| A | "I didn't quite get that. Can you ask again in plain words?" | no |
| B | the same | yes |
| C | a 90-word hand-written re-ask built from the author's own `/reask` requests | no |
| D | the same 90 words | yes |

## The preregistered outcome did not separate the cells

A run counts as **closed in one** only when every outcome grader passes. That happened in 2 of
27 B runs and in none of A, C or D:

| Cell | Closed in one | 95% CI |
|---|---|---|
| A | 0/27 | 0–12% |
| B | 2/27 | 2–23% |
| C | 0/27 | 0–12% |
| D | 0/27 | 0–12% |

H1 (B closes more runs than A) and H2 (B not worse than C) are **not shown**: B is ahead in one
scenario of nine and tied in the rest, sign test p = 1.0. The measure sits on the floor for every
cell, the long hand-written prompt included, which says the combined bar is stricter than any of
these re-asks can meet, not that they are equally useless. The graders were piloted on one reply
and amended (see deviations), but the planned controls that would have caught this (known-good
re-asks that must pass) were not run before the main run.

## What the graders show one by one (exploratory)

Not preregistered as the headline; computed after seeing the data. The share of outcome-grader
verdicts that passed, and each grader on its own:

| | A | B | C | D |
|---|---|---|---|---|
| **Outcome graders passed, mean** | 35% | **48%** | 35% | 49% |
| Facts a cold reader can state | 0/27 | 4/27 | 11/27 | 12/27 |
| Decisions a returning user can make, as their situation needs | 10/45 | **18/45** | 8/45 | 18/45 |
| Every open decision asked, none settled, ends on the asks | 11/27 | 11/27 | 0/27 | 6/27 |
| Does not recommend the option the trap makes wrong | 22/27 | **27/27** | 24/27 | 26/27 |
| Codes and session names explained (diagnostic) | 8/27 | 18/27 | 22/27 | 22/27 |
| User's own language (diagnostic, 3 scenarios) | 9/9 | 9/9 | 9/9 | 9/9 |
| **Median words** | 188 | **524** | 1,167 | 921 |
| Reading time at 238 words a minute | 0.8 min | 2.2 min | 4.9 min | 3.9 min |

Per scenario, outcome graders passed:

| Scenario | A | B | C | D |
|---|---|---|---|---|
| rate-limit-compacted | 50% | 83% | 42% | 50% |
| invoice-rounding | 27% | 60% | 7% | 53% |
| buried-status | 25% | 50% | 50% | 58% |
| heldout-a | 28% | 50% | 33% | 50% |
| heldout-b | 33% | 47% | 33% | 40% |
| mixed-language-ru | 47% | 47% | 27% | 67% |
| vector-index-unsure | 33% | 42% | 42% | 42% |
| orchestrator-stack | 20% | 20% | 33% | 47% |
| import-ux-ru | 50% | 33% | 50% | 33% |

- **B against A** (the same five words, with and without reask): ahead in 6 scenarios, behind in
  1, tied in 2; 13 points on average; sign test p = 0.125. Ahead on both held-out scenarios
  (+22 and +13 points), which were written by someone else and not looked at while the skill was
  tuned.
- **B against C** (five words against a 90-word hand-written prompt): ahead in 5, behind in 2,
  tied in 2; p = 0.45. C states more of the facts, but its replies run to a median of 1,167
  words, ask for none of the decisions in a way the grader accepts, and lead the returning user to
  the decision their situation needs less often (8/45 against 18/45). B gets there in less than
  half the words.
- **The trap.** In `invoice-rounding` the recorded question recommended the option the tax rule in
  the project rules out. Re-asked without reask, 2 of 3 replies still recommended it; with reask,
  none did. Across all scenarios reask never recommended a trap option (27/27).
- **Where reask did not help.** `import-ux-ru`, a decision about what end users see, scored lower
  with reask (33% against 50%), and `orchestrator-stack`, a decision left open from an earlier
  message plus a new one, did not move.

## Does the skill load when it should, and only then

| The user's reply after the question | Skill loaded |
|---|---|
| "What do you need from me here?" | 18/18 |
| "Agreed, go with your recommendation." | 0/18 |
| "Carry on, and open a PR at the end." | 0/18 |

The planned check that the reply to "agreed" stays within about 60 words failed in 18 of 18, but
it measured the wrong thing: the skill did not load in any of those runs, so it measured how much
the agent writes when it carries on with the work. It says nothing about reask.

## Limits

- Nine scenarios, three runs per cell. Nothing here is statistically significant.
- Agent, judge and scenario writers are all Claude models; the author of the skill designed the
  benchmark. The two held-out scenarios reduce, not remove, that bias.
- The fixture projects are synthetic, written in the shape of the author's real sessions.
- No human labels yet: the judge's verdicts have not been checked against people.
- **The fixture project was often out of the agent's sight.** The harness mounts it as an extra
  read-only directory, and in 21 of the 36 reply files at least one run says the working
  directory is empty or the files are not there. So "check the fact before you recommend" could
  mostly use only what the recorded session had already read. This touches every cell, and C and
  D most, since their prompt asks for that check by name. The next run should put the fixture in
  the working directory.

## Deviations from the preregistration

1. **Grader amendments after a one-run pilot**, before any main run: the decision grader no longer
   counts a question about a detail that would not change the choice; the all-decisions grader
   accepts decisions asked as the options of one question and treats a recommendation as advice;
   stage-2 facts were limited to decision-relevant substance (no ticket codes). The pilot
   scenario, `rate-limit-compacted`, had its stage 2 rewritten after the pilot reply was seen.
2. **3 runs per cell instead of 5**, to fit the time available.
3. **`codes-ru` is not in the run**: its chosen recording held a mistyped temporary path the
   sanitizer refused; the sanitizer was fixed, but the scenario was not run.
4. **The grader controls, field agreement, blind human labels and judge panel were not run.**
   They are still owed before "closed in one" or any grader is published as a measure of real
   understanding.
5. **Stage 2 of eight scenarios was committed about a minute after the main run started**; the run
   read the same files, and no re-ask had been seen before they were written.
6. **The first trigger run had two harness bugs** (a must-not-load check that could never pass,
   and a regex anchor JavaScript does not have); those cases were run again after the fix. The
   must-load case is from the first run.
7. **Known scenario problems**, found while writing stage 2 and left as they were:
   `vector-index-unsure`'s trap wording is close to an option a good re-ask may recommend;
   `mixed-language-ru` used the closest recording, as none met its select rule;
   `orchestrator-stack`'s second decision reads the persona's deadline more strictly than the
   persona states it.
