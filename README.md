# reask

[![ci](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml/badge.svg)](https://github.com/Nezhinskiy/reask/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/reask)](https://pypi.org/project/reask/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)

**Five letters, and you understand the decision.** Your agent asked you something and you cannot
answer it: you lost the context, the options are jargon, or you cannot see what actually differs
between them. Type `/reask`. The same question comes back written for someone who just walked in:
what is being built and why this decision matters now, every name from the session explained, the
pros and cons of every option, a recommendation, and how sure the agent is. Always in your
language.

```bash
npx skills add Nezhinskiy/reask --global --agent claude-code   # Claude Code
npx skills add Nezhinskiy/reask --global --agent codex         # Codex
npx skills add Nezhinskiy/reask --global --agent cursor        # Cursor
npx skills add Nezhinskiy/reask --global --agent gemini-cli    # Gemini CLI
```

These use the [Skills CLI](https://github.com/vercel-labs/skills). The Claude Code plugin, Python
and claude.ai routes are
[further down](https://github.com/Nezhinskiy/reask#more-ways-to-install). reask is an
[Agent Skill](https://agentskills.io): one file,
[`SKILL.md`](https://github.com/Nezhinskiy/reask/blob/main/skills/reask/SKILL.md).

## How to use it

**1. A question you cannot answer.** Type this, and nothing else:

```text
/reask
```

Installed as a Claude Code plugin, the command is `/reask:reask`. In Codex, type `$reask`. Plain
words work too: "ask again", "I don't get the question".

**2. Only the questions worth thinking about.** When Claude Code asks several questions in a form,
answer the easy ones as usual and write `/reask` in the Other field of the ones you want to think
through. Only those come back, and the answers you gave stay. Nothing gets longer where you did
not ask for it.

**3. Say what you need.** Anything after the command steers the re-ask:

```text
/reask show it from the user's side
/reask explain it with examples
/reask I'm a backend developer, not a designer
```

**Read how sure it is.** The recommendation says how firm it is, and that tells you where to spend
your attention. "Firm" means a fact settles it, and you can usually skim. "Leaning" or "a
close call" means a real fork: read it carefully, because a mistake would be here.

**It looks again before it recommends.** The agent argues against its own first lean and checks
the fact that lean rests on in your project. Sometimes a new option appears or the recommendation
changes, and it says so in one line. Even when you do not take the new option, you see the
decision more widely.

## Example

An agent is adding a required `region` column to a 40-million-row `orders` table, and stops to
ask three questions. This is one of them:

> **Rollout:** are you OK with the multi-step plan above, including a backfill script that runs
> outside the deploy job? Or does something like a maintenance window change things?

Asked by hand with "Not sure I follow. Can you rephrase it simply?", the agent comes back with:

> **Is the step-by-step plan OK?** If you'd prefer something else, like doing it all at once during
> a maintenance window, tell me.

With reask installed, the same words bring back:

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

Both replies are real output from Claude Opus 5.5 with reask 0.3.0 on a small test project, trimmed
to this one question. The first option here is new: the agent had not offered it before, and it
replaced its own earlier plan. That does not happen on every question, and the option is yours to
take or leave.

In Claude Code the question arrives with its answers as options to pick, the recommended one
first.

## More ways to install

Leaving off `--global` installs the skill into the current project instead, and `--agent '*'`
installs it for every agent the Skills CLI knows.

**Claude Code plugin:**

```text
/plugin marketplace add Nezhinskiy/reask
/plugin install reask@reask
```

A plugin's skills are namespaced, so installed this way it answers to `/reask:reask`, and to plain
requests such as "ask again". Updates arrive with `/plugin marketplace update reask`.

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

It does not ask questions of its own. Tools that interview you before a task starts decide *what*
to ask; reask works on a question the agent has already asked and you cannot yet answer.

## Troubleshooting

**`/reask` is not recognised.** The command depends on how you installed it: `/reask` with the
Skills CLI or Python, `/reask:reask` as a Claude Code plugin, `$reask` in Codex. Plain words work
in all of them: "ask again", "I don't get the question".

**It installed, but nothing happens.** Start a new session, so the agent picks up the new skill.
Then check that the file is there: `~/.claude/skills/reask/SKILL.md` for a global Claude Code
install. For the plugin, run `/plugin` and look for `reask`.

**It says nothing is pending.** The agent found no open question in this session, for example
because it has already moved on. Name the decision: `/reask the question about the cache key`.

**The re-ask misses what you need.** Say what is missing, and it re-asks with that in mind:
`/reask shorter, only what differs` or `/reask I still don't see the risk in option B`.

**Something else.** Open a
[skill behaviour issue](https://github.com/Nezhinskiy/reask/issues/new?template=skill_behaviour.yml)
with the transcript.

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

## License

[MIT](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)
