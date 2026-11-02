# reask benchmark v2: preregistration

Written and committed before any v2 history was recorded, before any re-ask was run and before
any change to `SKILL.md` that v2 is meant to measure. The commit that adds this file is the
**stage-1 freeze**; its hash goes into every v2 result. A change to this file, to a scenario's
truth, to a grader template or to `prompts.toml` after a result exists means every cell is run
again, and the README says so.

## What reask is for, and what this measures

reask is a tool the user reaches for by choice, on a hard question, after losing the thread: they
run many agent sessions at once, come back hours later, or return to a session that was compacted
or started by another session. In the author's sessions (two machines, 2026-09-29 to 2026-11-02),
a quarter of re-asks came after a compaction, and most came while several other sessions were
active.

The question this benchmark answers: **after one re-ask, can a person who lost the context make
every open decision, correctly, without asking another question; and how many words did that
take?**

It does not compare reask with the question as first asked: nobody re-asks a question they could
answer.

## Cells

The user's reply after the pending question is the same text in both arms of a pair. Nobody types
`/reask`: a command that does not exist in one arm would rig the comparison.

| Cell | The user's reply | Plugin |
|---|---|---|
| A | short: "I didn't quite get that. Can you ask again in plain words?" (5–9 words) | no |
| B | the same short reply; the skill loads on its own | yes |
| C | manual: the author's best hand-written re-ask, about 90 words, assembled from the arguments they actually typed after `/reask` before this benchmark existed | no |
| D | the same manual reply | yes |

Texts: [`prompts.toml`](prompts.toml). D exists because the harness runs every case with and without
the plugin; no claim rests on it. Every cell gets the same tools (`Read`, `Glob`, `Grep`, `Skill`)
and `max_turns` 20.

## Hypotheses

- **H1 (primary).** B closes more runs in one re-ask than A.
- **H2.** B is not worse than C: B's share of closed runs is at least C's minus 10 percentage
  points, and B's median words over closed runs are at most 1.2 times C's.
- **H3 (skill change).** When `SKILL.md` changes, B on the new version is not worse than B on the
  old: closed share at least the old minus 10 points, median words at most 1.1 times the old.
  Otherwise the change is reverted or reworked, and runs again.
- **H4 (triggers).** The skill does not load after "agreed, go with your recommendation" or "carry
  on, and open a PR at the end", and after "agreed" the reply stays within about 60 words; it does
  load after "what do you need from me here?".

## Primary outcome: closed in one

A run is **closed** when every one of its scenario's outcome graders passes:

- `facts`: a reader who has seen nothing else could state each fact on the scenario's list,
  including the trap fact;
- `decision-N`, one per open decision: a returning user who knows one thing about their own
  situation that the agent was never told (the scenario's persona) can choose without asking
  anything, and can see which option has the property their situation calls for. Some personas
  call for an option the agent is unlikely to recommend, so following the recommendation does not
  pass by itself;
- `all-decisions`: every open decision is asked (including one left open from an earlier message),
  none is settled by the agent, answers already given are not asked again, and the message ends on
  the asks;
- `no-trap-pick`: the message does not recommend the option the trap fact makes wrong.

`references` (every code and session name unpacked) and `language` (written in the user's own
language) run only in scenarios where they can fail. They mirror rules in `SKILL.md`, so they are
diagnostics, reported per cell, and not part of "closed".

Words are counted over the agent's final message. Reading time is shown as words / 238 per minute,
an estimate, not a measurement.

## Scenarios

Eight scenarios in [`scenarios/`](scenarios), each a `scenario.toml`, a fixture `project/` and,
once recorded, `history.jsonl`. Their mix follows the measured shapes of losing context:
compaction, an orchestrating session reading child sessions' reports, a decision left open from an
earlier message, a question buried in a status report, a domain the user is not expert in, a
decision about what end users see, English tooling with a Russian-speaking user, and a decision
made of ticket and rule codes. Two more, held out, are written after the skill is frozen and are
not looked at while it is tuned.

Stage 1 (this commit) fixes for each scenario: the steps that produce the pending question, the
rule that picks which recording counts, the trap (a fact in one fixture file that makes one option
wrong) and the persona.

## Recording

1. Each scenario runs in a scratch copy of its `project/`, with an empty `CLAUDE_CONFIG_DIR` (no
   user `CLAUDE.md`, memory, plugins or MCP servers), model `claude-opus-5-5`, read-only tools.
2. The `[record]` steps are sent in order. Recordings are repeated until one meets the scenario's
   `select` rule, up to five; every recording is kept locally, and the README names which one was
   used and how many were discarded.
3. `scripts/sanitize_history.py` turns the session into `history.jsonl`; it refuses to write if a
   home path, temp path, e-mail, token or system reminder is left, and a test scans every
   committed history for the same.

## Stage 2: truth from the recorded question

After recording and before any re-ask is run, each scenario's `[stage2]` is written from the
recorded question: the open decisions, the facts a cold reader must be able to state, answers
already given, and for each decision the persona decides, the property of the option it calls for.
Committed as the **stage-2 freeze**; its hash also goes into the results.

## Grader checks before any number is published

1. **Controls** (no agent; `grade_external.py`, the generalised `grade_original.py`): the recorded
   question itself and two to three deliberately broken re-asks per scenario (a fact removed, a
   decision dropped, the trap recommended) must fail; two to three hand-written good re-asks must
   pass. A grader that passes more than a third of its negative controls is dropped from "closed".
2. **Field agreement**: the "could you choose without asking" grader runs on the author's real
   re-asks (local only) and is compared with what the author actually did next (decided, or asked
   again). Reported as Cohen's kappa and sensitivity on the asked-again cases; aggregates only.
3. **Blind human labels**: 20–30 B/C pairs, order shuffled and cells hidden, labelled against the
   same checklists; a second labeller if one is available. Reported as human–judge kappa. Without
   agreement, "closed" is not published as the headline.
4. **Judge panel**: the harness judges with `claude-sonnet-5-5`; saved replies are re-judged with
   Haiku and Opus and agreement is reported. Same-family judging remains a stated limitation.

## Runs and analysis

- A one-case smoke run first, to fix the budget; the full run sets `--max-cost-usd`.
- 5 runs per case and arm. Agent `claude-opus-5-5`, judge `claude-sonnet-5-5`, three votes.
- Cells A–D on the frozen skill; B also on the previous release (H3); trigger cases separately,
  `--tag trigger --ablation none --runs 5`.
- Unit of analysis: the scenario. Published: a per-scenario table of closed shares and median
  words per cell; the paired B−A and B−C differences with an exact sign test over scenarios; Wilson
  intervals per cell; pass^k (all k runs closed) per cell; a closed-share against words plot.
- Exclusions: a run that hits `max_turns` or errors in the harness is re-run once and reported;
  nothing else is excluded.

## What this benchmark does not claim

- Statistical significance or generality beyond these scenarios, this agent, this judge and these
  two languages.
- That the returning-user grader measures a real person's understanding, unless check 2 or 3 shows
  agreement.
- That reask caused anything in the author's field data, which is observational.
- That the judges are free of bias; agent and judge are the same model family.
- Time saved for real users: reading time is an estimate.

The "about 90 words against 5" difference between C and B is a condition of the experiment, not a
result: anyone can save C as a command of their own. What B against C tests is whether the skill
does at least what a strong hand-written prompt does.

Run on 2026-11-02; what was done differently from this plan is listed under "Deviations" in
[`RESULTS.md`](RESULTS.md).
