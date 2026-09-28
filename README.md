# reask

[![ci](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml/badge.svg)](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/reask)](https://pypi.org/project/reask/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Nezhinskiy/reask/badge)](https://scorecard.dev/viewer/?uri=github.com/Nezhinskiy/reask)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Your agent asked you something and you cannot answer it.** You lost the context, the options
are jargon, or you cannot see what actually differs between them. Type `/reask`.

The agent asks the same question again, written for someone who just walked in: where the work
stands, one real example carried through every option, the pros *and* cons of each (the one it
recommends included), its recommendation, and one question you can answer. Under 500 words, in
your language.

It works in Claude Code, Codex, Cursor, Gemini CLI and any agent that reads
[Agent Skills](https://agentskills.io). The whole skill is one file: [`SKILL.md`](SKILL.md).

## Example

Mid-task, the agent asks:

> Should the price cache key include the locale, or should we normalise currency at read time?

You type `/reask`, and get:

> **Where we are and why this comes up.** We are adding a cache in front of the pricing API so
> product pages stop taking 800 ms. The cache is built; what is open is what a cache entry is
> keyed on, and nothing can be merged until that is decided. *Decided:* Redis, 10-minute expiry.
> *My assumption:* the 40 locales we ship today are the ones to plan for.
>
> **A live example.** SKU `A-1042` viewed from Berlin (`de-DE`, EUR) and from Vienna (`de-AT`,
> EUR):
>
> | | Key per locale | Normalise at read |
> |---|---|---|
> | Cache entries | 2 | 1 |
> | API calls on first views | 2 | 1 |
> | A later Austria-only price | works | needs a code change |
>
> **Options.**
> *Key per locale*: one entry per SKU per locale.
> Pros: correct if prices ever differ by country; no conversion code.
> Cons: about 40 locales means about 40 times the entries and cold-cache calls.
> *Normalise at read*: one entry per SKU in EUR, converted when read.
> Pros: 40 times fewer entries; one warm-up per SKU.
> Cons: wrong the day a country gets its own price; a rate-table lookup on every read.
>
> **What I recommend.** Key per locale. The pricing API already returns country-specific prices
> for 3 SKUs, so normalising would be wrong today, not someday; 40 entries per SKU is about 2 MB
> at our catalogue size. I would change my mind if those 3 prices turn out to be a data error.
>
> **The question.** Key the cache per locale (recommended), or normalise currency at read time?

## Install

### Claude Code plugin

```text
/plugin marketplace add Nezhinskiy/reask
/plugin install reask@reask
```

Updates arrive with `/plugin marketplace update reask`. Installed as a plugin, the skill is
namespaced and answers to `/reask:reask`; it also triggers on its own when you answer a question
with confusion.

### Skills CLI (Claude Code, Codex, Cursor, Gemini CLI and others)

```bash
npx skills add Nezhinskiy/reask --global --agent claude-code
```

Use `--agent '*'` for every agent the [Skills CLI](https://github.com/vercel-labs/skills)
supports, or leave off `--global` to install into the current project. Installed this way, the
skill answers to `/reask`.

### Python

```bash
uvx reask install
```

or `pipx run reask install`. This writes `~/.claude/skills/reask/SKILL.md`; `--project` writes
`./.claude/skills` instead and `--skills-dir PATH` any other location. A modified copy is not
overwritten without `--force`. `reask print` prints the skill and `reask uninstall` removes it.

### Claude.ai and Claude Desktop

Download `reask-skill.zip` from the [latest release](https://github.com/Nezhinskiy/reask/releases/latest)
and upload it under Settings > Capabilities > Skills.

### By hand

Copy [`SKILL.md`](SKILL.md) to `~/.claude/skills/reask/SKILL.md`, or into your agent's skill
folder.

## Why it works

Agents ask good questions in the wrong register: they have the whole session in context and
you do not. reask fixes the register, not the question. It keeps the decision yours (it never
starts on its default), states each option's downside at full strength, and ties the
recommendation to facts from your work, so you can overrule it with one reply.

## Contributing and security

Behaviour reports with a transcript are the most useful contribution; see
[CONTRIBUTING.md](CONTRIBUTING.md). Report vulnerabilities privately, as described in
[SECURITY.md](SECURITY.md). Every release is built in CI and carries a
[build provenance attestation](SECURITY.md#verifying-what-you-installed).

## License

[MIT](LICENSE)
