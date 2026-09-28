<!--
Conventional Commits title, describing intent:
  fix(skill): keep the recommended option's cons at full strength
not:
  update SKILL.md
-->

## What this changes, and why

<!-- The behaviour before and after. If it fixes something, describe the failure, not the patch. -->

## Evidence

<!--
For a SKILL.md change: a before and an after transcript of the same situation, and the agent and
model you ran them on. For code: what you ran, pasted, not paraphrased.
For each new assertion: the line of code you broke and the test that went red.
-->

## Checklist

- [ ] `uv run pytest --cov`, `ruff`, `mypy` and `scripts/check_skill.py` pass locally
- [ ] `SKILL.md` stays language-neutral and within its own word budgets
- [ ] A line under `## Unreleased` in `CHANGELOG.md`, if users would notice
- [ ] Not a security fix (if it is, see [SECURITY.md](../SECURITY.md) first)
