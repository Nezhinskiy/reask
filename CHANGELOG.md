# Changelog

Newest first. The release workflow publishes the section whose heading matches the tag as the
GitHub Release notes, so each `## X.Y.Z (date)` section is written for users.

## 0.1.0 (2026-09-29)

First release.

- The `/reask` skill: re-asks a pending question as a five-part briefing (where we are, a live
  example, options with pros and cons, a recommendation, one question), under 500 words, in the
  user's language.
- Five ways to install: the Claude Code plugin marketplace, the Skills CLI (`npx skills add`),
  the `reask` Python package, a zip for claude.ai, or copying `SKILL.md` by hand.
- `reask install`, `reask uninstall` and `reask print`. `install` writes to
  `~/.claude/skills/reask/`, to `./.claude/skills/reask/` with `--project`, or anywhere with
  `--skills-dir`, and refuses to overwrite a locally modified copy without `--force`.
