# Releasing reask

A release is a pushed `vX.Y.Z` tag. `.github/workflows/release.yml` checks the tag against the
sources, tests, builds and attests, then waits for one approval on the `pypi` environment before
uploading to PyPI through Trusted Publishing and creating the GitHub Release with the wheel,
the sdist and `reask-skill.zip` for claude.ai. There is no PyPI token anywhere.

The plugin marketplace and `npx skills` read the default branch, not the tag, so for those two
channels `main` is the release: whatever `SKILL.md` it carries is what they install. Claude Code
offers a plugin update when `.claude-plugin/plugin.json`'s `version` changes, which is why every
release bumps it along with the rest.

## 1. One-time setup (done)

These are in place; check them before every release, because none of them lives in the tree.

1. **The `pypi` environment**, with the maintainer as required reviewer and deployment limited
   to tags matching `v*.*.*`. Without it, GitHub auto-creates `pypi` with no rules and nothing
   waits for a human; `environment-gate` fails the run in that case rather than letting it
   through.
2. **A PyPI Trusted Publisher** for project `reask`: owner `Nezhinskiy`, repository `reask`,
   workflow `release.yml`, environment `pypi`.
3. **The `release tags` ruleset**: tags matching `v*.*.*` cannot be moved or deleted, with no
   bypass. A published version is permanent.
4. **The `main` ruleset**: no deletion or force-push; changes arrive through pull requests with
   a green `ci-ok`. The maintainer can bypass it for an emergency, and every bypass is logged.

```bash
gh api repos/Nezhinskiy/reask/environments/pypi --jq '[.protection_rules[].type]'   # ["required_reviewers","branch_policy"]
gh api repos/Nezhinskiy/reask/rulesets --jq '[.[] | .name]'                         # ["release tags","main"]
curl -sS -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/reask/json         # 404 before the first release, then 200
```

## 2. Cutting a release

1. **Open a release pull request** from a branch off current `main`:

   - Set the version in the three places written by hand: `pyproject.toml`,
     `.claude-plugin/plugin.json` and `metadata.version` in `SKILL.md`'s frontmatter
     (`reask.__version__` reads the installed metadata), then `uv sync` to refresh `uv.lock`.
   - Rename `## Unreleased` in `CHANGELOG.md` to `## X.Y.Z (YYYY-MM-DD)` and edit it for users:
     its body becomes the GitHub Release notes verbatim.

   ```bash
   uv run python scripts/check_skill.py               # "... one version everywhere: X.Y.Z"
   uv run python scripts/release_notes.py vX.Y.Z      # read what the Release will say
   ```

   Title it `chore(release): X.Y.Z`. Merging it ships the new `SKILL.md` to plugin and
   `npx skills` users; the tag below ships it to PyPI and the Release.

2. **Tag the merge commit and push the tag.** Final versions only: `release.yml` does not
   trigger on `v0.2.0-rc1`.

   ```bash
   git switch main && git pull
   uv run python scripts/check_skill.py --tag vX.Y.Z
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. **Approve and watch.** `build` runs first; `publish` and `github-release` then wait for the
   `pypi` approval (one approval starts both, one rejection stops both). `github-release` does
   not depend on `publish`, so a failed upload still leaves a Release.

   ```bash
   gh run watch "$(gh run list --workflow release --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
   ```

4. **Verify what shipped.**

   ```bash
   gh release view vX.Y.Z
   gh release download vX.Y.Z --pattern '*.whl' --dir /tmp/reask-release
   gh attestation verify /tmp/reask-release/*.whl --repo Nezhinskiy/reask
   uvx --refresh reask@X.Y.Z --version
   ```

## 3. When something fails

- **`build` fails on the version check or the tests.** Nothing was published. The tag ruleset
  keeps the tag where it is, so fix the sources in a pull request and release the next patch
  version; leave the failed tag in place.
- **`publish` fails on Trusted Publishing.** The pending publisher's fields do not match the
  workflow exactly (repository, workflow file name, environment name). Fix it on PyPI and re-run
  the failed job; the built artefacts are reused.
- **A published version is wrong.** PyPI never accepts the same version twice. Yank it on PyPI
  and release the next patch version.
