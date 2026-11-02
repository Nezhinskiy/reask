Answers kept from last time: **CI runs on GitHub Actions**, on every pull request and on every push to `main`.

**Shared context.** The CI is for `ledgerkit`, a small Python library of double-entry ledger helpers. On every change, CI will install the project, run the linter and run the tests. Nothing has been written yet, and the workflow file depends on the four answers below. The repo has a placeholder test and one database test. That test uses `postgresql`, a fixture (a helper pytest sets up before a test runs) from the pytest-postgresql plugin. The fixture needs a real Postgres database server.

---

### 1. Which Python versions should CI test?

**Context.** `pyproject.toml` declares `requires-python = ">=3.10"`, so anyone on 3.10 or newer can install it. According to the README, the two known users are the billing team on Python 3.10 and the data team on 3.13. Each version tested is one more CI job running in parallel.

**Options**
- **A. Only 3.10 and 3.13**
  - Pros: it tests exactly what your two real users run, and the oldest and newest ends catch almost all version breakage.
  - Cons: a break specific to 3.11, 3.12 or 3.14 would go unnoticed, even though the package claims to support them.
- **B. Every version from 3.10 to 3.14**
  - Pros: it backs up the `>=3.10` claim, and it shows in advance whether 3.14 works before the data team upgrades.
  - Cons: five jobs instead of two, each starting its own Postgres, for versions nobody is known to use.

**Recommendation:** A, leaning. Your only known users are on 3.10 and 3.13. The best argument for B is the `>=3.10` claim, but outside users aren't mentioned anywhere, and adding versions later is a one-line change.

**Question:** Should CI test only 3.10 and 3.13 (A), or every version from 3.10 to 3.14 (B)?

---

### 2. How should the database test get a Postgres server, and which Postgres version?

**Context.** The `postgresql` fixture doesn't connect to an existing database. It starts and stops its own temporary Postgres server using `pg_ctl`, the Postgres server-control program, so that program has to be installed wherever the tests run. Your developers' machines already meet this requirement if the test passes for them today.

**Options**
- **A. Install Postgres on the CI machine and leave the tests unchanged**
  - Pros: CI runs the tests exactly the way developers run them locally, and no test code changes.
  - Cons: the workflow has to point the plugin at the right `pg_ctl` path. That path is tied to the Postgres version, so it needs editing on each upgrade.
- **B. Run Postgres as a separate container next to the tests, and change the tests to connect to it** (using the plugin's `postgresql_noproc` fixture, which connects to an existing server instead of starting one)
  - Pros: choosing the Postgres version is a single image tag, which is the usual GitHub Actions pattern.
  - Cons: it changes the tests to fit CI. Developers would then need a Postgres server already running locally, or the tests behave differently on their machines.

**Recommendation:** A, leaning. It keeps CI and local runs identical and doesn't touch the tests. The best argument for B is easier version pinning, which costs one line in A. I haven't verified one assumption: that GitHub's standard Ubuntu machine has Postgres preinstalled. If it doesn't, A needs an extra install step, but it still works.

**Version:** CI should use the same major Postgres version as production, and I can't see which one production runs.

**Question:** Should CI use A or B? And which Postgres major version does production run (for example 16 or 17)?

---

### 3. What should CI use to install dependencies, and should exact versions be pinned?

**Context.** The test tools (pytest, pytest-postgresql, ruff) are listed in a `[dependency-groups]` section, a fairly new standard format. uv, a fast installer that replaces pip, reads it natively. pip only reads it from version 25.1, with `--group dev`. A lockfile (`uv.lock`) records the exact version of every dependency, so every CI run installs the same versions.

**Options**
- **A. uv, no lockfile**
  - Pros: fast installs, native support for your config, and every run gets the newest compatible `psycopg`, the same version your users get.
  - Cons: a new release of a dependency can turn CI red with no change on your side.
- **B. uv with a committed `uv.lock`**
  - Pros: CI results only change when your code or the lockfile changes.
  - Cons: users of a library don't use your lockfile, so CI can stay green while they hit a break from a new `psycopg` release. The lockfile also needs regular updates.
- **C. pip** (25.1 or newer)
  - Pros: no new tool for the team to learn.
  - Cons: slower, and it has no lockfile option without adding another tool.

**Recommendation:** A, leaning. This is a library, so CI should break when a new dependency release breaks it, because that's when your users break. The best argument for B is stable CI, but stability that hides problems your users hit is the wrong kind for a library.

**Question:** Should CI use uv without a lockfile (A), uv with `uv.lock` (B), or pip (C)?

---

### 4. What should CI enforce with ruff?

**Context.** Ruff is already in your dev tools, and it does two separate things. `ruff check` lints, meaning it flags likely bugs and bad patterns. `ruff format --check` fails if any file isn't formatted the way ruff would format it, so developers must run `ruff format` before pushing. The repo has no ruff settings, so ruff uses its defaults. It reads the minimum Python version from `requires-python` automatically.

**Options**
- **A. Lint only**
  - Pros: no new habits, and CI only fails on real problems.
  - Cons: formatting stays inconsistent and causes noisy diffs in review.
- **B. Lint and format check, with default settings**
  - Pros: consistent formatting with no style arguments, and with so little code today, switching costs almost nothing.
  - Cons: PRs go red over whitespace until everyone runs `ruff format`, or sets their editor to run it on save.
- Also possible: either option plus a `[tool.ruff]` section that picks extra rule sets. I'd skip it until a specific rule is wanted.

**Recommendation:** B, leaning. With almost no code yet, this is the cheapest moment to adopt a formatter. The best argument against B is the friction of red PRs, which disappears once editors format on save. If the team doesn't want that habit, choose A.

**Question:** Should CI run lint only (A), or lint plus the format check (B)?
