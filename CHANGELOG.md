# Changelog

Newest first. Every entry is written for users: a release's section becomes its GitHub Release
notes.

## 0.1.0 (2026-09-29)

First release.

- The `/reask` skill: re-asks a pending question as a five-part briefing (where we are, a live
  example, options with pros and cons, a recommendation, one question) in under 500 words and in
  the user's language, or as a short form when the question is a simple yes or no.
- Install it with the Skills CLI (`npx skills add Nezhinskiy/reask`), as a Claude Code plugin,
  with the `reask` Python package, as a zip for claude.ai, or by copying `SKILL.md`.
- `reask install`, `reask uninstall` and `reask print`. Neither `install` nor `uninstall`
  replaces or deletes a copy you have edited without `--force`, and neither follows a symbolic
  link inside the skills directory.
- Every release is built in CI from its tag and carries build provenance attestations.
