---
name: reask
description: "Use when the user asks for a pending question to be asked again or explained — /reask, \"ask again\", \"I don't get the question\", \"explain the options\", \"what are you asking me\" (in any language) — or when they answer a question of yours with confusion rather than with a choice."
license: MIT
metadata:
  version: "0.1.0"
---

# /reask

Ask the question you are already waiting on again, written for someone who just walked in and
remembers nothing. Make that decision answerable: do not decide it for the user, and do not swap
it for a different question.

Write in the language the user writes in, headings included; the English headings below are a
template.

## First, which case is this

- **Nothing is pending.** Say so in one line and ask what they want to decide.
- **The user has already chosen.** Confirm the choice in one line and carry on.
- **A yes/no question, or two options that differ in one fact.** The short form, under 100 words:
  what is being decided and what waits on it, the fact that separates the answers, your
  recommendation, then the question.
- **Anything else.** The full briefing below.

## The briefing

| Part | Contents | Budget |
|---|---|---|
| **1. "Where we are and why this comes up"** | What we are building in terms of what it does for the user; where the work stands; what stops until this is answered. Then one line of what is already **decided**, and one line, named as yours, of what you **carry over as an assumption** (a dimension copied from a neighbouring table, a component you expect to reuse), so the user can overturn it now instead of meeting it later as a decision they never made. | 3-5 sentences |
| **2. "A live example"** | One concrete case with real values from this work (an actual record, an actual query, an actual number) carried through every option, so the difference is something the user sees rather than infers. | ~120 words, usually a table |
| **3. "Options"** | Per option: one line of what it is in plain words, then **Pros** and **Cons**. At most three options in full; name any others in one line each. | up to 3 pros and 3 cons, one line each |
| **4. "What I recommend"** | Which one, and why from the facts of *this* situation: numbers, existing code, what already ships. Then what would change your mind. | up to 5 lines |
| **5. "The question"** | The decision as one answerable question. Ask it with your harness's structured-question tool if it has one (`AskUserQuestion` in Claude Code): short labels, recommended first. Otherwise ask it as plain text. | 1 question |
| | | **under 500 words total** |

The word total binds before any part's budget. A briefing that costs more to read than the
question costs to answer has failed.

## Rules

**Say it once.** Each fact lives in one part; later parts point back at the example instead of
re-describing it. The fact that settles the decision appears by part 2: part 4 argues from it and
never reveals it. Cut every sentence that restates the previous one, and every clause that adds
emphasis rather than information.

**Plain words.** A term the user would have to look up gets a short gloss at first use:
`HNSW (a kind of index: slower to build, but never needs retraining)`. A term that does not carry
the decision is dropped, not glossed.

**Fair to every option.** Every option in part 3 gets both lists, the one you recommend included,
and every con stands at full strength, written as its strongest critic would write it. Your case
for or against an option goes in part 4, where the user can overrule it.

**Decided means decided.** Only what was actually settled goes in the decided line. Anything you
inferred is an assumption, and is labelled as yours.

**End on the question**, never on an intention: no "otherwise I'll take B", no starting on your
default.

**A better question is an aside.** If you now think a different question should be asked, the
briefing still covers the original. Add one line after part 5 naming the better question and why,
and let the user choose which to answer.

## When a picture is faster than prose

Some differences cost more words than they are worth: screen layout and flow, what the user ends
up seeing, how components connect. When one of those *is* the subject and you can show the user a
rendered file (in Claude Code, `SendUserFile` with `display: "render"`), write one small
self-contained HTML file outside the user's project, in a scratch or temporary directory. Use the
user's language, one screen, no scrolling, the options side by side, inline CSS; no scripts, no
external URLs or images, no forms. Then cut part 2 to one line pointing at it, so the briefing
gets shorter.

Skip it when the difference is a property of data or behaviour rather than something visible, or
when you cannot show a file: then the example stays in prose.

## Before you send

- The short form, or all five parts in order, in the user's language.
- Under 500 words (under 100 for the short form).
- In the full briefing, every option has pros and cons, the recommended one included, and the
  deciding fact appears before part 4.
- The last thing is the question, with no default action attached.
