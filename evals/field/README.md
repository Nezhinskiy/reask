# reask in real use

The benchmark in [`../`](..) replays six questions. This page counts what reask did in real work:
every time it ran in the author's own Claude Code sessions, from the first release to the day this
page was written.

## Results, 2026-09-29 to 2026-11-02

There were 89 uses in 7 of the author's projects (code, research and data work, in English and
Russian). In 86 of them a decision was pending. reask was typed as `/reask` 53 times and loaded on
its own 33 times. Project names and content stay private; these counts are all that is published.

| After the re-ask… | Uses | Share |
|---|---|---|
| it offered an option the original question had not | 54 of 86 | 63% |
| …and recommended that new option | 39 of 86 | 45% |
| its recommendation changed from the original's | 27 of 86 | 31% |
| the author made the decision in the next message | 76 of 86 | 88% |
| the author was still confused and asked again | 2 of 86 | 2% |
| the author picked an option that first appeared in the re-ask (checked by hand) | at least 10 | – |

"New" is strict. A rewording, a sub-detail, or a merge of two options the question already listed
does not count. Examples from the log, paraphrased:

- Dropping an annotation engine for another tool plus direct reads of three databases, where the
  question asked only how to keep or replace that engine.
- Re-signing four commits with a no-reply address, a fix the question had not listed.
- Making a renumbering command warn about entries that name the old ID and leave them as they
  are, a behaviour the question had not listed.

**How it was counted.** `mine.py` read every session transcript and found each use, along with the
pending question, the re-ask and the author's next message. Uses copied into a resumed or forked
session were kept once. Scripted sessions run from a temp directory and the skill's own repository
were excluded. `classify.py` then asked `claude-sonnet-5-5` the rubric questions about each use.

The judge's verdict on *which* option the author then picked was unreliable: it often read a
second `/reask` or "explain more" as a choice. That row was checked by hand, and only clear picks
were counted. The other rows are the judge's verdicts. A hand check of a sample found them
plausible, but they are one model's reading.

**Limits.** These are one person's sessions, mostly on Claude Opus. Nobody can say how often the
option would have come up without reask. The benchmark's no-reask arm is the controlled answer to
that question.

## Count your own

```bash
python3 evals/field/mine.py ~/.claude/projects uses.jsonl          # your uses, stays local
python3 evals/field/classify.py uses.jsonl classified.jsonl         # one claude -p call per use
python3 evals/field/tally.py classified.jsonl                       # the counts
```

`classify.py` costs about 6 cents per use with Sonnet 5.5.
