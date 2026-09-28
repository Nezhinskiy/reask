# Contributing to reask

Thank you for helping. reask is small on purpose: one skill file and a thin installer. Most
valuable contributions are to the wording of [`SKILL.md`](SKILL.md), and they are judged by how
an agent behaves with the change, not by how the prose reads.

## Before you start

- **A bug in the skill's behaviour** (the agent re-asked badly, skipped a part, decided for you,
  wrote too much): open a [skill behaviour issue](https://github.com/Nezhinskiy/reask/issues/new?template=skill_behaviour.yml)
  with the transcript. A transcript is the reproduction.
- **A change to what the skill does**: open an issue first. The briefing's five parts and its
  word budget are deliberate, and a proposal is cheaper to discuss than a pull request.
- **A security problem**: see [SECURITY.md](SECURITY.md). Do not open a public issue.

## Changing `SKILL.md`

A pull request that changes the skill's wording should show the behaviour it fixes or adds:

1. **Before**: a transcript (or the relevant part) where the current skill misbehaves.
2. **After**: the same situation with your change, on the same agent and model.
3. **Which agent and model** you ran it on.

Keep to the file's own rules: say each thing once, plain words, every option keeps its hearing.
The skill must stay language-neutral: examples and headings in English, with the instruction to
answer in the user's language intact. The description in the frontmatter decides when agents
load the skill; change it only with an example of the trigger it fixes.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Nezhinskiy/reask && cd reask
uv sync
```

Every check CI runs:

```bash
uv run pytest --cov                   # 100% line and branch coverage is required
uv run ruff check . && uv run ruff format --check .
uv run mypy                           # strict
uv run python scripts/check_skill.py  # one SKILL.md, valid frontmatter, one version everywhere
npx --yes skills@1.7.0 add . --list   # the Skills CLI finds exactly one skill
npx --yes @anthropic-ai/claude-code@2.1.284 plugin validate .claude-plugin/plugin.json --strict
uvx zizmor@1.30.1 --pedantic .github/workflows   # only if you touched a workflow
```

To try your working copy in Claude Code, install it as a local plugin:

```text
/plugin marketplace add ./
/plugin install reask@reask
```

or copy it over your installed skill with `uv run reask install --force`.

### Tests

Test behaviour, not incidental shape: each assertion should fail if the behaviour it names
breaks. When you add an assertion, break the line of code it protects and watch the test go red
before you trust it; say in the pull request which line you broke.

## Pull requests

- One change per pull request. Title in [Conventional Commits](https://www.conventionalcommits.org/)
  form, describing intent: `fix(skill): keep the recommended option's cons at full strength`,
  not `update SKILL.md`.
- Add a line under a new `## Unreleased` heading at the top of [CHANGELOG.md](CHANGELOG.md) if
  users would notice the change.
- Do not bump versions; that happens at release time ([RELEASING.md](RELEASING.md)).
- `main` is protected: pull requests merge by squash once the `ci-ok` check is green.

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE)
and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
