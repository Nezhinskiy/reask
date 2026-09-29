# Releasing reask

A release is a pushed `vX.Y.Z` tag on `main`. `.github/workflows/release.yml` checks the tag
against `main` and the sources, tests, builds and attests, then waits for one approval on the
`pypi` environment before uploading to PyPI through Trusted Publishing and creating the GitHub
Release with the wheel, the sdist and `reask-skill.zip` for claude.ai. There is no PyPI token
anywhere.

The plugin marketplace and `npx skills` read `main`, not the tag, so for those two channels
merging is the release: whatever `skills/reask/SKILL.md` `main` carries is what they install.
Claude Code offers a plugin update only when `.claude-plugin/plugin.json`'s `version` changes,
which is why every release bumps it.

## Repository settings

The release depends on settings that live outside the tree. This is their expected state:

```bash
gh api repos/Nezhinskiy/reask/environments/pypi --jq '[.protection_rules[].type]'   # ["required_reviewers","branch_policy"]
gh api repos/Nezhinskiy/reask/rulesets --jq '[.[] | .name]'                         # ["main","release tags"]
```

1. **The `pypi` environment**: the maintainer as required reviewer, deployments limited to tags
   matching `v*.*.*`.
2. **The PyPI Trusted Publisher** for project `reask`: owner `Nezhinskiy`, repository `reask`,
   workflow `release.yml`, environment `pypi`.
3. **The `release tags` ruleset**: tags matching `v*.*.*` cannot be moved or deleted, with no
   bypass. A published version is permanent.
4. **The `main` ruleset**: no deletion or force-push; changes arrive through squash-merged pull
   requests with a green `ci-ok`. The admin role can bypass it, and every bypass is logged.

## Cutting a release

1. **Open a release pull request** from a branch off current `main`, titled
   `chore(release): X.Y.Z`:

   - Set the version in `skills/reask/SKILL.md`'s `metadata.version` (the Python package reads
     its version from there) and in `.claude-plugin/plugin.json`.
   - Rename `## Unreleased` in `CHANGELOG.md` to `## X.Y.Z (YYYY-MM-DD)` and edit it for users:
     its body becomes the GitHub Release notes verbatim.

   ```bash
   uv run python -m scripts.check_skill              # "... one version everywhere: X.Y.Z"
   uv run python -m scripts.release_notes vX.Y.Z     # what the Release will say
   ```

2. **Tag the merge commit and push the tag.** Final versions only: `release.yml` does not
   trigger on `v0.2.0-rc1`.

   ```bash
   git switch main && git pull
   uv run python -m scripts.check_skill --tag vX.Y.Z
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. **Approve and watch.** `build` runs first; `publish` and `github-release` then wait for the
   `pypi` approval (one approval starts both, one rejection stops both). `github-release` does
   not depend on `publish`, so a failed upload still leaves a Release.

   ```bash
   gh run watch "$(gh run list --workflow release --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
   ```

4. **Verify what shipped**, with the commands in
   [SECURITY.md](SECURITY.md#verifying-what-you-installed), then:

   ```bash
   uvx --refresh reask@X.Y.Z --version
   ```

## When something fails

- **`build` fails on the `main` check, the version check or the tests.** Nothing was published.
  The tag ruleset keeps the tag where it is, so fix the sources in a pull request and release the
  next patch version; leave the failed tag in place.
- **`publish` fails on Trusted Publishing.** The publisher's fields on PyPI do not match the
  workflow exactly (repository, workflow file name, environment name). Fix them on PyPI and
  re-run the failed job; the built artefacts are reused.
- **A published version is wrong.** PyPI never accepts the same version twice. Yank it on PyPI
  and release the next patch version.
