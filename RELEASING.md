# Releasing reask

A release is a pushed `vX.Y.Z` tag. `.github/workflows/release.yml` checks the tag against the
sources, tests, builds and attests, then waits for one approval on the `pypi` environment before
uploading to PyPI through Trusted Publishing and creating the GitHub Release. There is no PyPI
token anywhere.

## 1. One-time setup

Do all three before the first tag. Without the environment, GitHub auto-creates `pypi` with no
rules and nothing waits for a human; `environment-gate` fails the run in that case rather than
letting it through.

1. **The `pypi` environment, with you as required reviewer.** Settings → Environments → New
   environment `pypi` → Required reviewers → add yourself; Deployment branches and tags →
   Selected → add the tag rule `v*.*.*`.
2. **A PyPI pending publisher.** On pypi.org: Your account → Publishing → Add a new pending
   publisher → GitHub, with project `reask`, owner `Nezhinskiy`, repository `reask`, workflow
   `release.yml`, environment `pypi`. A pending publisher does not reserve the name; the first
   successful upload does.
3. **A tag ruleset**, so a published tag cannot be moved or deleted: Settings → Rules →
   Rulesets → New tag ruleset, target `v*.*.*`, rules "Restrict updates" and "Restrict
   deletions", no bypass.

Check them before every release:

```bash
gh api repos/Nezhinskiy/reask/environments/pypi --jq '.protection_rules | length'   # >= 1
curl -sS -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/reask/json         # 404 before the first release, then 200
```

## 2. Cutting a release

1. **Be on `main`, current and green.** The workflow builds from the tag.

   ```bash
   git switch main && git pull
   uv run pytest -q
   ```

2. **Set the version** in `pyproject.toml` (the only place it is written by hand;
   `reask.__version__` reads the installed metadata), then refresh the lock:

   ```bash
   uv sync
   ```

3. **Write the changelog section.** Add `## X.Y.Z (YYYY-MM-DD)` at the top of `CHANGELOG.md`.
   Its body becomes the GitHub Release notes verbatim, so write it for users.

   ```bash
   uv run python scripts/check_version.py          # "one version everywhere: X.Y.Z"
   git commit -am "chore(release): X.Y.Z"
   git push origin main
   ```

4. **Tag and push the tag.** Final versions only: `release.yml` does not trigger on `v0.2.0-rc1`.

   ```bash
   uv run python scripts/check_version.py --tag vX.Y.Z
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. **Approve and watch.** `build` runs first; `publish` and `github-release` then wait for the
   `pypi` approval (one approval starts both, one rejection stops both). `github-release` does
   not depend on `publish`, so a failed upload still leaves a Release.

   ```bash
   gh run watch "$(gh run list --workflow release --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
   ```

## 3. When something fails

- **`build` fails on the version check.** The tag names a version the sources do not carry. Delete
  the tag locally and remotely (the ruleset blocks deleting it only once you have set one; if so,
  pick the next version instead), fix the sources, and tag again.
- **`publish` fails on Trusted Publishing.** The pending publisher's fields do not match the
  workflow exactly (repository, workflow file name, environment name). Fix it on PyPI and re-run
  the failed job; the built artefacts are reused.
- **A published version is wrong.** PyPI never accepts the same version twice. Yank it on PyPI
  and release the next patch version.
