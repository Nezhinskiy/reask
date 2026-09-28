# reask

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill for the moment an agent asks
you something and you cannot answer it: you lost the context, the options are jargon, or you
cannot see what actually differs between them.

Type `/reask` (or say "I don't get the question") and the agent asks the same question again as
a short, self-contained briefing:

1. **Where we are** — what is being built, what is blocked, what is already decided, and which
   assumptions the agent is carrying over.
2. **A live example** — one real case from the work, carried through every option.
3. **Options** — each with pros *and* cons, including the recommended one.
4. **Recommendation** — grounded in this situation, plus what would change the agent's mind.
5. **The question** — one answerable question, with the recommended choice first.

It stays under 500 words and answers in whatever language you write in.

## Install

```bash
uvx reask install
```

or `pipx run reask install`, or `pip install reask && reask install`.

This writes `~/.claude/skills/reask/SKILL.md`. Use `--project` to install into
`./.claude/skills` instead, or `--skills-dir PATH` for any other location. A modified copy is not
overwritten without `--force`.

Other commands: `reask print` prints the skill, `reask uninstall` removes it.

Manual install works too: copy [`src/reask/SKILL.md`](src/reask/SKILL.md) to
`~/.claude/skills/reask/SKILL.md`.

## License

MIT
