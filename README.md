# reask

An agent skill for the moment an agent asks you something and you cannot answer it: you lost
the context, the options are jargon, or you cannot see what actually differs between them.

Type `/reask` (or say "I don't get the question") and the agent asks the same question again as
a short, self-contained briefing:

1. **Where we are**: what is being built, what is blocked, what is already decided, and which
   assumptions the agent is carrying over.
2. **A live example**: one real case from the work, carried through every option.
3. **Options**: each with pros *and* cons, including the recommended one.
4. **Recommendation**: grounded in this situation, plus what would change the agent's mind.
5. **The question**: one answerable question, with the recommended choice first.

It stays under 500 words and answers in whatever language you write in. The whole skill is one
file, [`SKILL.md`](SKILL.md), following the [Agent Skills](https://agentskills.io) format.

## Install

### Claude Code plugin

```text
/plugin marketplace add Nezhinskiy/reask
/plugin install reask@reask
```

Updates arrive with `/plugin marketplace update reask`. Installed as a plugin, the skill is
namespaced and answers to `/reask:reask`; it also triggers on its own when you are confused by a
question.

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

## License

MIT
