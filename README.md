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

Measured with Claude Code's plugin eval harness on six real stalls: an agent without reask has
asked a question, and the user replies "Sorry, I stepped away and lost the thread. I don't
understand what you're asking me. Ask it again." Every case runs with reask loaded and without
it, and the user's reply is the same in both. Nobody types `/reask`; the skill loaded on its own
in 18 of 18 runs. Claude Opus 5.5 answers, Claude Sonnet 5.5 judges, and there are 3 runs per arm.

| The re-ask… | Without reask | With reask |
|---|---|---|
| can be followed by someone who never saw the session | 10/18 | **18/18** |
| gives every option's downside, the recommended one's too | 6/18 | **13/18** |
| grounds its recommendation in a project fact | 16/18 | **18/18** |
| ends with the decisions to answer, each a one-word reply | 7/18 | **10/18** |
| keeps an easy yes/no under 200 words | **3/3** | 0/3 |

Overall the score goes from 0.60 to 0.81. The price is length: a median of 238 words becomes 548,
and each reply costs about 11 cents more with Opus 5.5. Two weak spots are still open. An easy
yes/no comes back at about 330 words, where SKILL.md promises about 150. And when several
questions are bounced, their asks are spread through one long reply. Every reply, the method and
the command to run it yourself are in
[`evals/`](https://github.com/Nezhinskiy/reask/tree/main/evals).

## Example: the same moment, with and without reask

From the benchmark's `reliability-plan` case. The agent is asked to plan a sprint from a folder of
tickets, an ADR and an RFC, and stops to ask two questions. The user replies that they lost the
thread. Both replies below are real, unedited output, from the median-scoring run of each arm.

Without reask, the agent's own re-ask is good: it gets the numbers and the conflict right. What
reask adds is what a reader coming in cold needs to decide:

- **The recommended option's downside.** Without reask, option A comes with its upside only. With
  reask, it comes with its cons, including one the agent found by looking again: if Postgres also runs on a single
  primary, checkout just moves to a different single point of failure.
- **What would change its mind,** and the strongest argument against its own pick.
- **What is decided and what is assumed** ("ADR-7's 6 days come out of these same 10 days. The
  docs don't say who does that work").
- **Every term explained:** p99 and SLO, not just the ticket codes.

<details>
<summary>Without reask (score 0.60, 286 words)</summary>

> No problem, here's the question again.
>
> **The situation:** You asked me to plan this sprint's reliability work. You have 10 dev-days, but the work in docs/ adds up to 16:
>
> - **PLAT-412** (8 days): move the session store from Redis Sentinel to Redis Cluster. This is meant to prevent another INC-301, the 47-minute checkout outage on Oct 3.
> - **PLAT-415** (2 days): add p99 latency alerts per endpoint.
> - **ADR-7** (6 days left, due Dec 15): move checkout to v2, which stores sessions in Postgres instead of Redis.
>
> **The catch:** Once ADR-7 is done, checkout no longer uses Redis at all. Only the admin panel does. So PLAT-412 would spend 8 days hardening Redis for something checkout is about to stop using.
>
> **Question 1: Which work goes into this sprint?**
>
> - **A (my recommendation):** ADR-7 + PLAT-415 = 8 days, with 2 to spare. Drop PLAT-412 or shrink it to just the admin panel. This prevents another INC-301 by moving checkout off Redis instead of hardening Redis.
> - **B:** PLAT-412 + PLAT-415 = 10 days. ADR-7 gets no time this sprint, which puts the Dec 15 deadline at risk.
> - **C:** ADR-7 comes out of a different team's or budget's time, not these 10 days. If so, let me know, and I'll reconsider whether PLAT-412 is worth doing at all.
>
> **Question 2: Which uptime target should I plan for?**
>
> A draft proposal (RFC-3) would raise checkout's target from 99.5% to 99.9%. That cuts the allowed downtime from about 3.6 hours a month to about 43 minutes. The head of product hasn't approved it yet. Should I plan for 99.9% anyway, or stick with the current 99.5%?
>
> A short answer like "A, 99.5%" is all I need.

</details>

<details>
<summary>With reask (score 0.80, 585 words)</summary>

> I'm asking two things before I plan the sprint's reliability work. The plan depends on the answers.
>
> ## Question 1: Which work goes into this sprint?
>
> **Context.** You have 10 dev-days across two engineers. Three items compete for them:
>
> - **PLAT-412** (8 days): move the session store from Redis Sentinel to Redis Cluster. Sentinel has a single primary server, and that primary caused **INC-301**, a 47-minute checkout outage on Oct 3. Cluster has no single primary.
> - **PLAT-415** (2 days): add alerts when an endpoint's p99 latency gets too high. p99 is the speed of the slowest 1% of requests.
> - **ADR-7** (6 days left): an accepted decision to retire checkout v1 by Dec 15. Checkout v2 keeps sessions in Postgres instead of Redis. Once it's done, only the admin panel uses Redis for sessions.
>
> All three add up to 16 days, which is 6 more than you have. ADR-7 also makes PLAT-412 much less useful, because once checkout is off Redis, hardening Redis mainly protects the admin panel.
>
> **Decided:** ADR-7 is accepted and due Dec 15.
> **My assumption:** ADR-7's 6 days come out of these same 10 days. The docs don't say who does that work.
>
> **Options**
>
> - **A. ADR-7 + PLAT-415 (8 days, 2 spare)**
>   - Pros: takes checkout off Redis, which removes INC-301's cause for checkout. It's also faster than PLAT-412 (6 days vs 8).
>   - Pros: keeps the Dec 15 date on track.
>   - Cons: the admin panel stays on Redis Sentinel with its single primary.
>   - Cons: the docs don't say how Postgres is set up. If it also runs on one primary, checkout moves to a different single point of failure.
> - **B. PLAT-412 + PLAT-415 (10 days)**
>   - Pros: attacks the exact component that failed in INC-301.
>   - Cons: 8 days spent on infrastructure that checkout stops using once ADR-7 ships.
>   - Cons: no ADR-7 work this sprint, so Dec 15 is at risk.
> - **C. ADR-7 is staffed separately**
>   - If someone else does ADR-7, you have all 10 days. The real question then becomes whether PLAT-412 is worth 8 days just to protect the admin panel.
>
> **Recommendation:** A, leaning. It removes the cause of INC-301 from checkout sooner and doesn't waste 8 days. The strongest argument against it is that B fixes the failure directly. But that fix stops mattering for checkout once ADR-7 lands. Two things would change my mind: ADR-7 being staffed separately (option C), or Postgres having the same single-primary weakness.
>
> **Which do you want: A, B, or C?**
>
> ## Question 2: Which availability target should I plan against?
>
> **Context.** Checkout's availability target, or SLO, is 99.5% today. That allows about 3.6 hours of downtime a month. **RFC-3** proposes raising it to 99.9%, which allows about 43 minutes. That's less than INC-301's 47 minutes, so one outage like it would use up the whole month. RFC-3 is still a draft waiting for sign-off from the head of product.
>
> The target affects how hard I push on reliability items and what I put in A's 2 spare days. It doesn't change the answer to Question 1.
>
> **Options**
>
> - **99.5% (current)**
>   - Pros: it's the target in force today.
>   - Cons: the plan may fall short if RFC-3 is approved mid-sprint.
> - **99.9% (proposed)**
>   - Pros: prepares for where things are likely headed.
>   - Cons: commits capacity to a target nobody has approved.
>
> **Recommendation:** 99.5%, firm, because RFC-3 isn't signed off. I'd note 99.9% as a stretch goal.
>
> **Should I plan against 99.5% or 99.9%?**

</details>

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

## License

[MIT](https://github.com/Nezhinskiy/reask/blob/main/LICENSE)
