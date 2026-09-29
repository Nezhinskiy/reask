---
name: reask
description: "Use when the user asks for a pending question to be asked again or explained — /reask, \"ask again\", \"I don't get the question\", \"explain the options\", \"what are you asking me\" (in any language) — or when they answer a question of yours with confusion rather than with a choice."
license: MIT
metadata:
  version: "0.3.0"
---

# /reask

Ask the question you are already waiting on again, so that someone who just walked in, and has
nothing but this message, can decide. `/reask` on its own means: I have lost the context; give me
everything I need to choose. Make the decision answerable: do not decide it for the user, and do
not swap it for a different question.

Write in the language the user writes in; the English labels below are a template.

## Which questions

- **Several questions were asked together** (a multi-question form, a numbered list): re-ask only
  the ones the user bounced with `/reask` or with confusion, and keep the answers they already
  gave. Give the shared context once, then each question as its own block. The last block gets
  the same depth as the first.
- **Nothing is pending:** say so in one line and ask what they want to decide.
- **The user has already chosen:** confirm the choice in one line and carry on.

## First, re-check your recommendation

Your lean when you first asked was formed before you laid the options out. Test it before you
write anything:

1. Argue for the strongest alternative as if you had to ship it.
2. Name the fact your recommendation rests on. If you have not verified it and a quick,
   read-only look would settle it, look now, at the source itself (the records, the config, a
   command's output), not at a comment or a name that describes it. Change nothing and do not
   start the work. Before deciding it cannot be checked, search the project once for where that
   fact would live. If it still cannot be checked, say which fact is unchecked and make it what
   would change your mind.
3. Decide again. The answer may be your first lean, another option, or a better option that
   surfaced while you argued. A new option joins the options, marked as new, with its pros and
   cons, and becomes one of the answers in the question.
4. Say how sure you are: firm, leaning, or a close call.
5. Report what you found as facts in their parts, never as the story of checking. If the
   recommendation differs from what you leaned to when you asked, add one line that names the
   fact that changed it. If it did not change, say nothing about the re-check.

## What every re-ask contains

For each question, in this order, with the part labels in bold:

1. **Context.** Always, and first. What we are building and what it does for the user; where
   the work stands; what waits on this answer. Then what is already **decided**, and what you
   **carry over as an assumption**, named as yours, each only when there is a real one. Every
   reference is unpacked where it first appears (see **References carry their content** below).
   State facts, not how you found them.
2. **A live example**, when the options' pros and cons alone do not show the difference, and
   always for a close call: one concrete case with real values from this work (an actual record,
   query or number) carried through every option, usually as a small table.
3. **Options.** Every option, the one you recommend included, with **Pros** and **Cons**: one
   line per item, the strongest first, and only as many as change the decision. Each con at full
   strength, as the option's strongest critic would put it. At most three options in full; name
   any others in one line each. Mark as new only an option that was not in the original question.
4. **Recommendation.** Which option, how sure you are, and why, from the facts of this situation.
   The evidence grows as your confidence falls:
   - **firm:** the fact that settles it;
   - **leaning:** that fact, plus the strongest argument against your pick and why it does not
     win;
   - **close call:** the facts on each side and what would tip it. The live example is required.
5. **The question.** The decision as one answerable question, asked fresh, with no preamble or
   lean carried over from the original wording. Ask it with your harness's structured-question
   tool if it has one (`AskUserQuestion` in Claude Code), all re-asked questions in one call:
   short labels, recommended first. Otherwise ask it as plain text.

## How deep

Depth follows the question, not the number of options. Give more context and more evidence when
the question uses ideas the user must hold at once, when the decision reaches beyond this step,
and when you are less than firm. A firm answer on familiar ground needs two or three sentences of
context and no example, about 150 words in all; a design choice you only lean on can take 500.

A re-ask never carries less than the original question did: every fact the original gave is
still in it, now explained. Past about 600 words for one question, it is really two questions:
say so and split it.

## Rules

**Say it once.** Each fact lives in one place; later parts point back instead of re-describing.
The fact that settles the decision appears before the recommendation argues from it. Cut every
sentence that restates the previous one, and every clause that adds emphasis rather than
information.

**References carry their content.** A reference by number or code (task 6b, TD-237, BR-161, rule
D1, §8, PR 3a) comes with what it says, as far as it bears on this decision, so the user never has
to open it: not "per D1", but "D1, the spec's rule that the lookup must hold at 2,000 products per
user". The same goes for a name from this session (a component, a constant, a feature, "the
review") and for the source of a number (who measured it, on what). If you do not know what a
reference says, read it now or leave it out; a name alone explains nothing.

**Plain words.** A term the user would have to look up gets a short gloss at first use:
`HNSW (a kind of index: slower to build, but never needs retraining)`. A term that does not carry
the decision is dropped, not glossed.

**Decided means decided.** Only what was actually settled goes in the decided line. Anything you
inferred is an assumption, and is labelled as yours.

**End on the question**, never on an intention: no "otherwise I'll take B", no starting on your
default.

**A better question is an aside.** If you now think a different question should be asked, the
re-ask still covers the original. Add one line after the question naming the better one and why,
and let the user choose which to answer. A better *option* for the same question is not an aside:
it goes through step 3 of the re-check.

## When a picture is faster than prose

Some differences cost more words than they are worth: screen layout and flow, what the user ends
up seeing, how components connect. When one of those *is* the subject and you can show the user a
rendered file (in Claude Code, `SendUserFile` with `display: "render"`), write one small
self-contained HTML file outside the user's project, in a scratch or temporary directory. Use the
user's language, one screen, no scrolling, the options side by side, inline CSS; no scripts, no
external URLs or images, no forms. Then replace the live example with one line pointing at it.

Skip it when the difference is a property of data or behaviour rather than something visible, or
when you cannot show a file: then the example stays in prose.

## Before you send

Read it as someone who has seen nothing but this message:

- They understand every word, and know what is being built and why this decision matters now.
- Every numbered reference and session name says what it is, not only what it is called.
- Every option has pros and cons, the recommended one included.
- The evidence matches your confidence.
- Nothing the original question said is missing.
- Every bounced question got the same depth, and the re-ask ends on the question.
