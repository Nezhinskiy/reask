---
name: reask
description: "Use when the user asks for a pending question to be asked again or explained — /reask, \"ask again\", \"I don't get the question\", \"explain the options\", \"unclear\" (in any language) — or when they answer a question of yours with confusion rather than with a choice. Trigger: /reask"
---

# /reask

Ask the question you are already waiting on again, written for someone who just walked in and
remembers nothing. The user wants that decision made answerable — not decided for them, not
swapped for a better question.

Write in the language the user writes in, headings included; the headings below are English
only as a template.

## The briefing

| Part | Contents | Budget |
|---|---|---|
| **1. "Where we are and why this comes up"** | What we are building in terms of what it does for the user; where the work stands; what stops until this is answered. Then one line of what is already **decided**, and one line — named as yours — of what you **carry over as an assumption** (a dimension copied from a neighbouring table, a component you expect to reuse), so the user can overturn it now instead of meeting it later as a decision they never made. | 3-5 sentences |
| **2. "A live example"** | One concrete case with real values from this work — an actual record, an actual query, an actual number — carried through every option, so the difference is something the user sees rather than infers. | ~120 words, usually a table |
| **3. "Options"** | Per option: one line of what it is in plain words, then **Pros** and **Cons**. Both lists for every option, including the one you recommend — write its cons as if arguing against it. | ≤3 pros, ≤3 cons, one line each |
| **4. "What I recommend"** | Which one, why from the facts of *this* situation — numbers, existing code, what already ships — and what would change your mind. | ≤5 lines |
| **5. "The question"** | The decision as one answerable question, then `AskUserQuestion` with short labels, recommended first. | 1 question |
| | | **under 500 words total** |

A briefing that costs more to read than the question costs to answer has failed.

## Rules

**Say it once.** Each fact lives in one part; later parts point back at the example instead of
re-describing it. Cut every sentence that restates the previous one, and every clause that adds
emphasis rather than information.

**Plain words.** A term the user would have to look up gets a short gloss at first use —
`HNSW (a kind of index: slower to build, but never needs retraining)`. A term that does not
carry the decision is dropped, not glossed.

**Every option keeps its hearing.** An option you would dismiss still gets its line and both
lists in part 3; your case against it goes in part 4, where the user can overrule it.

**Both sides at the same strength.** "Its downside is smaller than I said" is part 4. In part 3
the con stands at full strength.

**Settled means decided, not inferred.** Only what was actually decided goes in the decided line.

**End on a question**, never on an intention — no "otherwise I'll take B", no starting by default.

**A better question goes in part 5.** Parts 1-4 still cover the original as asked; part 5 asks the
better one and says in one line what changed.

## When a picture is faster than prose

Some differences cost more words than they are worth: screen layout and flow, what the user ends
up seeing, how components connect. When one of those *is* the subject, write a small
self-contained HTML file into the session scratchpad directory and surface it with `SendUserFile`
(`display: "render"`), then cut part 2 to one line pointing at it. The user's language, one
screen, no scrolling, options side by side, inline CSS, no libraries. It replaces the prose it
saves, so the briefing gets shorter.

Skip it when the difference is a property of data or behaviour rather than something visible — a
diagram of three table layouts teaches less than the worked example.
