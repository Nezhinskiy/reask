# reask

[![ci](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml/badge.svg)](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/reask)](https://pypi.org/project/reask/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)

**Your agent asked you something and you cannot answer it.** You lost the context, the options
are jargon, or you cannot see what actually differs between them. Type `/reask`.

The agent asks the same question again, written for someone who just walked in: what is being
built and why this decision matters now, every name from the session explained, the pros *and*
cons of every option (the one it recommends included), its recommendation, and one question you
can answer. `/reask` on its own is enough. The harder the question and the less sure the agent
is, the more context and evidence you get; an easy call it is sure of stays short. Asked several
questions at once, you can bounce just the ones you cannot answer. Always in your language.

Before it recommends anything, the agent argues against its own first lean and checks the fact
that lean rests on in your project. When the check changes its mind, or turns up a better option,
it says so in one line.

reask is an [Agent Skill](https://agentskills.io): one file,
[`SKILL.md`](https://github.com/Nezhinskiy/reask/blob/main/skills/reask/SKILL.md), that Claude
Code, Codex, Cursor, Gemini CLI and other agents that read the format can load.

## Install

**Any agent, with the [Skills CLI](https://github.com/vercel-labs/skills):**

```bash
npx skills add Nezhinskiy/reask --global
```

It asks which agents to install into; `--agent claude-code` (or `--agent '*'`) skips the
question, and leaving off `--global` installs into the current project.

**Claude Code plugin:**

```text
/plugin marketplace add Nezhinskiy/reask
/plugin install reask@reask
```

A plugin's skills are namespaced, so this one answers to `/reask:reask`. Updates arrive with
`/plugin marketplace update reask`.

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

## Example

Mid-task, the agent asks:

> Should the price cache key include the locale, or should we normalise currency at read time?

You type `/reask`, and get:

> **Where we are and why this comes up.** We are putting a cache in front of the pricing API so
> product pages stop taking 800 ms. The cache works; what is open is what each entry is keyed
> on, and nothing merges until that is decided. The pricing API already returns a
> country-specific price for 3 SKUs. *Decided:* Redis, 10-minute expiry. *My assumption:* the 40
> locales we ship today are the ones to plan for.
>
> **A live example.** SKU `B-2210`, one of those 3, costs €49 in Germany and €45 in Austria.
> Viewed from Berlin (`de-DE`) and then from Vienna (`de-AT`):
>
> | | Key per locale | Normalise at read |
> |---|---|---|
> | Cache entries | 2 | 1 |
> | API calls on first views | 2 | 1 |
> | Price shown in Vienna | €45 | €49 |
>
> **Options.**
> *Key per locale*: one entry per SKU per locale.
> Pros: every country sees its own price; no conversion code.
> Cons: 40 times the entries; 40 cold-cache API calls per SKU instead of one.
> *Normalise at read*: one entry per SKU in euros, converted when read.
> Pros: 40 times fewer entries; one warm-up per SKU.
> Cons: shows the wrong price for those 3 SKUs today; a rate-table lookup on every read.
>
> **What I recommend.** Key per locale. Normalising shows Vienna €49 for `B-2210` today, not
> someday; 40 entries per SKU is about 2 MB at our catalogue size. I would change my mind if
> those 3 prices turn out to be a data error.
>
> **The question.** Key the cache per locale (recommended), or normalise currency at read time?

In Claude Code the question arrives with both answers as options to pick, the recommended one
first. This example was written by hand to show the format; a real briefing is built from your
session's facts.

## Why it works

Agents ask good questions in the wrong register: they have the whole session in context and
you do not. reask fixes the register, not the question. It keeps the decision yours (it never
starts on its default), states each option's downside at full strength, and ties the
recommendation to facts from your work, so you can overrule it with one reply.

## Contributing and security

Behaviour reports with a transcript are the most useful contribution; see
[CONTRIBUTING.md](https://github.com/Nezhinskiy/reask/blob/main/CONTRIBUTING.md). Report
vulnerabilities privately, as described in
[SECURITY.md](https://github.com/Nezhinskiy/reask/blob/main/SECURITY.md). Every release is built
in CI and carries a
[build provenance attestation](https://github.com/Nezhinskiy/reask/blob/main/SECURITY.md#verifying-what-you-installed).

## License

[MIT](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)
