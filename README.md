# reask

[![ci](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml/badge.svg)](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/reask)](https://pypi.org/project/reask/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)

**Your agent asked you something and you cannot answer it:** you lost the context, the options
are jargon, or you cannot see what actually differs between them. Type `/reask`.

```bash
npx skills add Nezhinskiy/reask --global --agent claude-code   # Claude Code
npx skills add Nezhinskiy/reask --global --agent codex         # Codex
npx skills add Nezhinskiy/reask --global --agent cursor        # Cursor
npx skills add Nezhinskiy/reask --global --agent gemini-cli    # Gemini CLI
```

These use the [Skills CLI](https://github.com/vercel-labs/skills); the plugin, Python and
claude.ai routes are
[further down](https://github.com/Nezhinskiy/reask#more-ways-to-install).

The agent asks the same question again, written for someone who just walked in: what is being
built and why this decision matters now, every name from the session explained, the pros *and*
cons of every option (the one it recommends included), its recommendation, and one question you
can answer. The harder the question and the less sure the agent is, the more context and
evidence you get; an easy call it is sure of stays short. Asked several questions at once, you
can bounce just the ones you cannot answer. Always in your language.

Before it recommends anything, the agent argues against its own first lean and checks the fact
that lean rests on in your project. When the check changes its mind, or turns up a better option,
it says so in one line.

reask is an [Agent Skill](https://agentskills.io): one file,
[`SKILL.md`](https://github.com/Nezhinskiy/reask/blob/main/skills/reask/SKILL.md), that any agent
reading the format can load.

## Does it help?

When you cannot answer your agent's question, you can answer anyway, ask by hand ("I didn't
quite get that, ask again in plain words"), or use reask. The
[benchmark](https://github.com/Nezhinskiy/reask/tree/main/evals) compares the three on six real
pending questions, with Claude Code's plugin eval harness. Claude Opus 5.5 answers, Claude Sonnet
5.5 judges, and there are 3 runs per arm. With reask installed, the hand-written re-ask loaded the
skill on its own in 18 of 18 runs.

| The message you have to decide from… | Answer anyway (the question as asked) | "Ask again in plain words" | reask |
|---|---|---|---|
| can be followed by someone who never saw the session | 0/6 | 7/18 | **17/18** |
| gives every option's downside, the recommended one's too | 0/6 | 5/18 | **16/18** |
| grounds its recommendation in a project fact | 4/6 | 15/18 | **18/18** |
| ends with the decisions to answer, each a one-word reply | 1/6 | 7/18 | **10/18** |

A plain re-ask makes the question shorter by dropping facts. reask makes it longer by putting
them back: a median of 207 words becomes 567, at about 9 cents more per reply with Opus 5.5.

**It also looks at the problem again.** Before recommending, reask argues against its own first
lean and re-checks the fact that lean rests on. In the author's own sessions, 86 re-asks across
7 projects from Sep 29 to Nov 2, 2026:

- **63%** offered an option the original question did not have.
- **31%** changed the agent's recommendation.
- **88%** were followed by a decision in the very next message.
- In at least 10 of them, the author chose the option that first appeared in the re-ask.

The counting scripts are in
[`evals/field/`](https://github.com/Nezhinskiy/reask/tree/main/evals/field), so you can run them
on your own sessions. Two weak spots are still open: an easy yes/no comes back at about 290 words,
where SKILL.md promises about 150, and when several questions are bounced, their asks are spread
through one long reply.

## Example: the same question, three ways

From the benchmark's `orders-migration` case. An agent was asked to add a required `region`
column to a 40-million-row `orders` table, and stopped to ask three questions. All three texts
below are real, unedited output.

<details>
<summary>The original question (364 words)</summary>

> I looked through the repo and need your decisions before writing anything. The repo is just `db/schema.sql`, `app/orders.py` and `OPS.md`.
>
> **What the repo shows**
> - `orders` has about 40M rows and takes about 25k inserts/hour at peak. `customers.billing_country` is `char(2) NOT NULL`.
> - `app/orders.py:2` says region will be "`customer.billing_country` mapped through `REGIONS`". `REGIONS` isn't defined anywhere in the repo.
> - Migrations run inside the deploy job, which times out after 10 minutes (DEPLOY-3). The replica lag alarm fires at 30 s, and a 6-minute table rewrite on `payments` caused INC-212.
> - TAX-19 needs `region` by Dec 1, and reports can treat a missing region as "unknown" until then.
>
> That rules out one migration that adds the column, backfills and sets NOT NULL. A single `UPDATE` on 40M rows would run past the 10-minute timeout and hit the replica lag alarm, much like INC-212.
>
> **What I'd propose** (Postgres 15), in this order:
> 1. **Migration:** add `region` as a nullable column with no default. This only changes metadata, so it's instant.
> 2. **App:** `create_order` starts writing `region` on every new order.
> 3. **Backfill:** a separate script, run outside the deploy job, that fills old orders in small batches by id range. It pauses between batches and watches replica lag.
> 4. **Migration:** add `CHECK (region IS NOT NULL) NOT VALID`, then `VALIDATE CONSTRAINT`. Validating doesn't block writes.
> 5. **Migration:** `SET NOT NULL`, which uses the validated check to skip a full table scan. Then drop the check.
>
> **What I need from you**
> 1. **The `REGIONS` mapping:** where does it live, and what are the region values (e.g. `EU`/`NA`/`APAC`, tax jurisdictions)? Should a country with no mapping fail the order, get a fallback like `'UNKNOWN'`, or something else?
> 2. **Old orders:** filling them from the customer's *current* billing country gives the wrong region if a customer has moved. Is that acceptable for TAX-19, or does tax need the country as it was at order time? If so, is there another source for it?
> 3. **Rollout:** are you OK with the multi-step plan above, including a backfill script that runs outside the deploy job? Or does something like a maintenance window change things?
>
> I'll stop here until you answer.

</details>

<details>
<summary>After "Not sure I follow. Can you rephrase it simply?" without reask (254 words)</summary>

> Sure, here's the plain version.
>
> **The problem:** `orders` has about 40 million rows. Filling in `region` for all of them at once is slow, and on a big table that kind of change can block new orders while it runs. Your notes say the deploy job gives up after 10 minutes, and something similar already caused an outage (INC-212). So I can't do this as one migration.
>
> **What I suggest:** split it into small, safe steps:
> 1. Add the `region` column as optional (empty allowed). This takes a second.
> 2. Change the app so every new order gets a region.
> 3. Fill in the old orders a little at a time with a separate script, outside the deploy.
> 4. Once every row has a value, make the column required (NOT NULL).
>
> Reports can treat an empty region as "unknown" in the meantime, which your notes allow until Dec 1.
>
> **Three questions for you:**
> 1. **What are the regions?** The code says to map the country "through `REGIONS`", but that list doesn't exist in the repo. Which country goes to which region? And what should happen with a country that isn't on the list?
> 2. **Old orders:** I'd take the region from the customer's billing country as it is *now*. If a customer has moved since an old order, that order gets their new region. Is that OK for the tax report?
> 3. **Is the step-by-step plan OK?** If you'd prefer something else, like doing it all at once during a maintenance window, tell me.

</details>

<details>
<summary>The same words with reask installed (824 words)</summary>

> Here are the same three questions in simpler terms.
>
> **The setup.** You want a new `region` column on `orders` that is always filled in (NOT NULL). The tax report needs it by Dec 1, four weeks from today. Until then, reports can show a missing region as "unknown".
>
> `orders` is big and busy: about 40 million rows, and up to about 25,000 new orders an hour. Database changes run inside the deploy job, which gets cut off after 10 minutes. Last month a 6-minute rewrite of the `payments` table stopped writes and caused an outage. So filling 40 million rows in one step during a deploy is risky.
>
> Nothing has been written yet.
>
> ---
>
> ### Question 1: What exactly goes in `region`?
>
> **Context.** The only hint is a comment in `app/orders.py`: region is "billing_country mapped through REGIONS". `REGIONS` doesn't exist in the repo. It's in no file I could see, and the repo has only three files. Billing country is a 2-letter code like `DE` or `US`.
>
> **Options**
> - **A. Store the country code itself** (`DE` stays `DE`). *New.*
>   - Pros: nothing to maintain, and every order gets a valid value.
>   - Cons: if the tax report needs groups like "EU", every report has to do the grouping itself.
> - **B. Map countries to groups** (`DE` becomes `EU`), using a list you give me. A country that isn't on the list gets `UNKNOWN`.
>   - Pros: matches the code comment, and the report gets the groups directly.
>   - Cons: someone has to keep the list up to date, and a country missing from it gets labelled `UNKNOWN`, which shows up as unknown in the tax report.
> - **C. Map as in B, but refuse to create an order whose country isn't on the list.**
>   - Pros: no bad data, ever.
>   - Cons: a missing list entry blocks real customers from ordering.
>
> **Recommendation:** B, leaning. Grouping by region seems to be the intent, and the report already accepts "unknown". This depends on what tax actually needs: if TAX-19 wants plain countries, A is better.
>
> ---
>
> ### Question 2: Which country do old orders get?
>
> **Context.** Old orders have to be filled in using the customer's billing country *as it is today*. The database keeps no history of past countries.
>
> **Example:** a customer ordered in 2024 while living in Germany, then moved to the US in 2025. Their 2024 order would be labelled US.
>
> **Options**
> - **A. Use today's country.**
>   - Pros: possible right now with the data we have.
>   - Cons: orders from customers who have moved get the wrong region, and that error ends up in a tax report.
> - **B. Use a historical source of the country at order time** (invoices, another system), if one exists.
>   - Pros: correct.
>   - Cons: I don't know if such a source exists. It isn't in this repo.
>
> **Recommendation:** A, leaning, because B has no data source I can see. I can't check how many customers have moved. If tax needs the country at the time of the order, you'd need B.
>
> ---
>
> ### Question 3: How should the change roll out?
>
> **Context.** The new column has to exist without locking the table for minutes. One useful fact: Postgres can add a column with a fixed default value instantly, without rewriting the table.
>
> **Options**
> - **A. Add it filled with `UNKNOWN`, then fill it in gradually.** *New.* Add the column as NOT NULL with default `UNKNOWN`, which is instant. The app then writes the real region on new orders. A separate script outside the deploy job fills old orders in small batches. Afterwards, remove the default.
>   - Pros: three steps, and the column is never empty.
>   - Cons: until the script finishes, `UNKNOWN` can mean either "not filled yet" or "country not on the list".
> - **B. My earlier plan.** Add the column empty, fill it in gradually, then make it NOT NULL with a safe two-step check.
>   - Pros: an empty value clearly means "not filled yet".
>   - Cons: five steps and more chances to slip.
> - **C. One step during a maintenance window.**
>   - Pros: simplest.
>   - Cons: orders stop for the length of the window, and it may not finish within the 10-minute deploy limit.
>
> **Recommendation:** A, leaning. It replaces my earlier pick (B) because adding a column with a fixed default is instant, so the column can be NOT NULL from the start. B's advantage only matters while the fill-in script is running.
>
> ---
>
> **Your answers:**
> 1. Should `region` hold the country code (A), a group from a list you'll give me (B), or a group with orders blocked for unlisted countries (C)?
> 2. Should old orders use today's country (A), or is there a source for the country at the time of the order (B)?
> 3. Should the rollout be: add filled with `UNKNOWN` and fill in gradually (A), add empty and enforce later (B), or one step in a maintenance window (C)?

</details>

The plain re-ask is easier to read, but it drops what you need to choose. Its first question is
open-ended, with no options to pick from, and no choice comes with a downside. With reask, each
question comes with its context, options, pros and cons and a recommendation, and the reply
closes with all three asks in one list.

It also brings a new option. reask re-checked how Postgres adds a column and proposed adding
`region` as NOT NULL with the default `UNKNOWN`, which is instant, then filling old rows in
batches. That replaced its own earlier five-step plan, and it said so. This is the best of three
runs and the only one that found the new option. The other two scored 0.6, against 0.2 for every
plain re-ask.

In the interactive Claude Code UI the question arrives with its answers as options to pick, the
recommended one first.

## More ways to install

Leaving off `--global` installs the skill into the current project instead, and
`--agent '*'` installs it for every agent the Skills CLI knows.

**Claude Code plugin:**

```text
/plugin marketplace add Nezhinskiy/reask
/plugin install reask@reask
```

A plugin's skills are namespaced, so installed this way it answers to `/reask:reask` (or to
plain requests such as "ask again"). Updates arrive with `/plugin marketplace update reask`.

**Python**, for Claude Code:

```bash
uvx reask install
```

or `pipx run reask install`. This writes `~/.claude/skills/reask/SKILL.md` (under
`$CLAUDE_CONFIG_DIR` if you set it); `--project` writes `./.claude/skills` instead and
`--skills-dir PATH` any other location. `reask print` prints the skill and `reask uninstall`
removes it. Neither command overwrites or deletes a copy you have edited unless you pass `--force`.

**claude.ai and Claude Desktop:** download `reask-skill.zip` from the
[latest release](https://github.com/Nezhinskiy/reask/releases/latest) and upload it under
Settings > Capabilities > Skills.

**By hand:** copy `skills/reask/SKILL.md` into a `reask/` folder in your agent's skills
directory.

## Why it works

Agents ask good questions in the wrong register: they have the whole session in context and
you do not. reask fixes the register, not the question. It keeps the decision yours (it never
starts on its default), states each option's downside at full strength, and ties the
recommendation to facts from your work, so you can overrule it with one reply.

It does not ask questions of its own. Tools that interview you before a task starts decide
*what* to ask; reask works on a question the agent has already asked and you cannot yet answer.

## Contributing and security

Behaviour reports with a transcript are the most useful contribution; see
[CONTRIBUTING.md](https://github.com/Nezhinskiy/reask/blob/main/CONTRIBUTING.md). Report
vulnerabilities privately, as described in
[SECURITY.md](https://github.com/Nezhinskiy/reask/blob/main/SECURITY.md). Every release is built
in CI and carries a
[build provenance attestation](https://github.com/Nezhinskiy/reask/blob/main/SECURITY.md#verifying-what-you-installed).

## Privacy

reask collects nothing and sends nothing anywhere. The plugin is a set of instructions: following
them, your agent may read files in your project to check a fact before it recommends an option,
and may write one HTML file to a temporary directory to show you a layout. It has no hooks, no MCP
servers and makes no network calls. The `reask` Python package writes, and on `uninstall`
removes, only `SKILL.md` in the skills directory you point it at.

The repository also holds developer scripts in `evals/field/` that count reask uses in your own
Claude Code transcripts. The plugin never loads or runs them; they run only when you start them,
and keep their output on your machine.

## License

[MIT](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)
