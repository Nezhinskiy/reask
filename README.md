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

## Example

This is real output, trimmed only where marked `[…]`: Claude Code 2.1.312 with Opus 5.5, on a
scratch copy of this repository. The task was to fix the Install section of this README; before
editing, the agent asked:

> **The decision: which route leads for Claude Code?** A. A Skills CLI one-liner leads, and the
> plugin moves down as an alternative. B. The plugin stays a first-class Claude Code route, and
> the hook mentions both names. […] A or B?

Typing `/reask` turned that into:

> **Context.** I'm editing the Install section of the reask README, from the audit's
> nice-to-haves in `AUDIT.md`. There are two fixes. The first adds one copy-paste install line
> per agent, so readers can see at a glance that reask works in their tool. The second deals with
> a naming mismatch. The README's opening line says "Type `/reask`." But one of the five install
> routes, the Claude Code plugin (`/plugin install reask@reask`), adds a prefix to the skill's
> name, so it answers only to `/reask:reask`. Every other route gives the plain `/reask`.
> Nothing is edited yet; the section's order depends on your answer.
>
> *Decided:* the per-agent lines will use the Skills CLI's `-a claude-code`, `-a codex`,
> `-a cursor` and `-a gemini-cli`, each with `--global`. […] *My assumption:* you will still
> submit the plugin to the Anthropic plugin directory, since the audit's first blocker, the
> missing plugin icon, exists to prepare that submission.
>
> A fact that softens either choice: the skill also starts on plain phrases like "ask again" or
> "I don't get the question". So a plugin user who types the wrong command name can still reach
> it.
>
> **A live example.** What each kind of reader copies and types:
>
> | Reader arrives from | Copies | Types `/reask` | Works? |
> |---|---|---|---|
> | GitHub or the megathread, under A | Skills CLI line for Claude Code | `/reask` | yes |
> | The plugin directory, under A | `/plugin install` | `/reask` (from the opening line) | no, needs `/reask:reask` |
> | The plugin directory, under B | `/plugin install` | the opening line names both | yes |
>
> **Options.**
>
> *A. The Skills CLI line for Claude Code goes first, and the plugin moves down as an
> alternative.* A short note in the plugin part says it answers to `/reask:reask`.
> - Pros: the first command most readers copy matches the opening line, and that line stays short.
> - Cons: plugin-directory users read an opening line that is wrong for them. The plugin is also
>   the route you're about to promote.
>
> *B. The plugin stays a first-class Claude Code route, and the opening line names both
> commands*, e.g. "Type `/reask` (`/reask:reask` if you installed the plugin)."
> - Pros: correct for every reader from the first line, and the plugin keeps its built-in updates.
> - Cons: the opening line gets clunkier, and the mismatch is explained rather than avoided.
>
> **Recommendation.** A, though I'm leaning rather than firm. reask isn't listed in the directory
> yet, so for now every reader comes through GitHub, where A is right. The strongest case for B
> is that the directory becomes your main channel after you submit. It doesn't win yet, because
> the plain-phrase trigger and the note in the plugin part cover those users. What would change
> my mind is directory installs overtaking GitHub ones, and nobody can measure that yet.
>
> **The question.** For Claude Code, should the README lead with the Skills CLI line and keep
> the opening line as `/reask` (A, recommended), or keep the plugin first-class and name both
> commands in the opening line (B)?

The answer was A, which is the layout of this page. In the interactive Claude Code UI the question
arrives with both answers as options to pick, the recommended one first.

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

## License

[MIT](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)
