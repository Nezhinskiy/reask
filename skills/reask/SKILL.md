---
name: reask
description: "Use when the user asks for a pending question to be asked again or explained — /reask, \"ask again\", \"I don't get the question\", \"explain the options\", \"what are you asking me\" (in any language) — or when they answer a question of yours with confusion rather than with a choice."
license: MIT
metadata:
  version: "0.2.0"
---

# /reask

Ask the question you are already waiting on again, written for someone who just walked in and
remembers nothing. Make that decision answerable: do not decide it for the user, and do not swap
it for a different question.

Write in the language the user writes in, headings included; the English headings below are a
template. If nothing is pending, say so in one line and ask what they want to decide. If the user
has already chosen, confirm the choice in one line and carry on.

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
   surfaced while you argued. A new option joins the options, marked as new, with its costs, and
   becomes one of the answers in the question.
4. Say how sure you are: firm, leaning, or a close call. A close call is an honest answer; say
   what would tip it.
5. Report what you found as facts in their parts, never as the story of checking. If the
   recommendation differs from what you leaned to when you asked, add one line that names the
   fact that changed it. If it did not change, say nothing about the re-check.

## Then size it to what the user is missing

Pick the size, then write exactly its parts, in this order.

**Small**, for a yes/no question or two options the user can picture once the context is named:
one sentence naming what is decided and the fact that separates the answers; one line per
option, `name: what it buys; what it costs`; one sentence with your recommendation, how sure you
are, and why; the question. About 60 words, never over 100:

> The nightly export can read from the replica or the primary. The replica lags up to 30 s
> (`ops/alerts.yml`), and the export reads only yesterday's rows.
> - Replica: no load on the primary; data up to 30 s old, which yesterday's rows never are.
> - Primary: always current; competes with checkout traffic at 02:00.
>
> I recommend the replica, firmly. Replica (recommended) or primary?

**Medium**, for three or more options, or options that trade off on more than one axis: up to
three sentences on what is decided, what it serves and what waits on it; the options, each as one
line in the small form or, when they trade off on more than one axis, as **Pros** and **Cons**
lists of one-line items; your recommendation in up to three lines; the question. At most three
options in full, a new one included; name any others in one line each. Under 250 words, no
headings.

**Full**, when the user has lost the thread entirely or the difference needs a worked example to
be seen: the parts below, under headings, under 500 words.

| Part | Contents | At most |
|---|---|---|
| **"Where we are"** | What we are building, in terms of what it does for the user; where the work stands; what stops until this is answered. Then what is already **decided**, and what you **carry over as an assumption**, named as yours, each only if there is one. | 5 sentences |
| **"A live example"** | One concrete case with real values from this work (an actual record, an actual query, an actual number) carried through every option, so the user sees the difference rather than infers it. | ~120 words, usually a table |
| **"Options"** | Per option, a line of what it is, then **Pros** and **Cons**. At most three in full; name any others in one line each. | 3 pros and 3 cons each |
| **"What I recommend"** | Which option; why, from the facts of this situation; how sure you are; what would change your mind. | 5 lines |
| **"The question"** | See below. | 1 question |

In every size, the question is the decision as one answerable question, asked fresh, with no
preamble or lean carried over from the original wording. Ask it with your harness's
structured-question tool if it has one (`AskUserQuestion` in Claude Code): short labels,
recommended first. Otherwise ask it as plain text.

## Rules

**Say it once.** Each fact lives in one place; later parts point back instead of re-describing.
The fact that settles the decision appears before the recommendation argues from it. Cut every
sentence that restates the previous one, and every clause that adds emphasis rather than
information.

**Plain words.** A term the user would have to look up gets a short gloss at first use:
`HNSW (a kind of index: slower to build, but never needs retraining)`. A term that does not carry
the decision is dropped, not glossed.

**Fair to every option.** Every option states its cost, the one you recommend included, at full
strength, as its strongest critic would put it. Your case for or against an option goes in the
recommendation, where the user can overrule it.

**Decided means decided.** Only what was actually settled goes in the decided line. Anything you
inferred is an assumption, and is labelled as yours.

**End on the question**, never on an intention: no "otherwise I'll take B", no starting on your
default.

**A better question is an aside.** If you now think a different question should be asked, the
re-ask still covers the original. Add one line after the question naming the better one and why,
and let the user choose which to answer. A better *option* for the same question is not an aside:
it goes through step 3 above.

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

- The re-ask has exactly the parts of the size you picked, and is under its ceiling.
- Every option states its cost, the recommended one included.
- The recommendation went through the re-check. A changed view has its one line; a new option is
  in the options and in the question.
- The last thing is the question, in the user's language, with no default action attached.
