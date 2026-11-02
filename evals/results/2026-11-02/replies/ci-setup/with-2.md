Questions 1 and 6 are settled. Here are 2–5 again, with more explanation.

**Context (applies to all four).** I'm setting up GitHub Actions for `ledgerkit`, a small Python library that two internal teams use. On every PR and every push to `main`, CI will run the tests and a style check. I haven't written anything yet. These four answers decide what the workflow file contains.

- **Decided:** GitHub Actions, triggered on PRs and pushes to `main`.
- **Repo facts:** `pyproject.toml` allows Python 3.10 and newer. The library depends on `psycopg` (the Postgres driver). Dev tools are pytest, pytest-postgresql (a pytest plugin that provides a database to tests) and ruff (a linter and formatter). There are two test files. One of them, `test_ledger.py`, asks for a real Postgres database.

---

### Q2. Which Python versions should CI test?

**Context.** CI runs the tests once per version. The README says billing uses 3.10 and the data team uses 3.13. 3.11 and 3.12 sit between them, and 3.14 is the newest release. Your `pyproject.toml` lets anyone install on any of them.

**Options**
- **A. Only 3.10 and 3.13**
  - Pros: covers exactly the two versions your users run. Two jobs per run.
  - Cons: a break that shows up only on 3.11 or 3.12 would go unnoticed. That's rare, because both ends pass.
- **B. 3.10, 3.11, 3.12 and 3.13**
  - Pros: tests every version between your users.
  - Cons: twice the jobs, and each one sets up Postgres. It doesn't protect either team any better.
- **C. (new) 3.10, 3.13 and 3.14**
  - Pros: shows you early when the data team's next upgrade would break something.
  - Cons: nobody uses 3.14 today, so a failure there could block a PR over a problem no user has.

**Recommendation: A, leaning.** These are the versions that matter to real users. The best case for B is that `requires-python >=3.10` promises every version. But if 3.10 and 3.13 both pass, the versions in between almost always do too.

**Which Python versions should CI test: A, B or C?**

---

### Q3. How should the tests get a Postgres database, and which Postgres version?

**Context.** `test_ledger.py` uses pytest-postgresql's `postgresql` fixture (a fixture is a helper that pytest hands to a test). That fixture **starts its own Postgres server** with the `pg_ctl` program. So the Postgres software has to be installed on the CI machine, not just reachable. Right now the test body is empty (`...`), so nothing actually queries the database yet.

| | What CI does | Test code | What a developer needs locally |
|---|---|---|---|
| **A** | Install Postgres on the CI machine | No change | Postgres installed (same as now) |
| **B** | Run Postgres in a separate container that CI starts next to the job | Switch to the `postgresql_noproc` fixture, which connects to an already-running server | A Postgres server running (e.g., in Docker) |

**Options**
- **A. Install Postgres on the CI machine**
  - Pros: no test changes. Tests run the same way in CI and on laptops.
  - Cons: depends on the CI machine having Postgres installed and the plugin finding `pg_ctl`. I haven't checked that here. It could take an extra setup step.
- **B. Separate Postgres container**
  - Pros: the usual GitHub Actions pattern, and picking the Postgres version is a one-line change.
  - Cons: changes the test code, and how developers run tests, just to suit CI.

**Recommendation: A, leaning.** It keeps the tests as they are. B's strongest point is easy version pinning, but A can pin a version too by installing that version. On the Postgres version: it should match what billing and the data team run in production. I don't know that, and the repo doesn't say. If you don't know either, I'd use 16, which I believe GitHub's Ubuntu machines come with (not verified).

**Should tests get Postgres via A (installed on the CI machine) or B (container, with a test change)? And which Postgres major version do billing and the data team run?**

---

### Q4. Which tool should CI use to install dependencies, and should exact versions be pinned?

**Context.** The dev tools are listed in a newer `pyproject.toml` section (`[dependency-groups]`). Older pip versions can't read it. uv, a fast pip replacement, reads it natively. A lockfile (`uv.lock`) records the exact version of every dependency, so every CI run installs the same thing.

**Options**
- **A. uv, no lockfile**
  - Pros: reads the dev tools directly. CI installs the latest allowed versions, which is what the two teams get when they install `ledgerkit`.
  - Cons: a new release of `psycopg` or pytest can turn CI red with no change on your side.
- **B. uv, with a committed `uv.lock`**
  - Pros: reproducible runs. CI only changes when you change the lockfile.
  - Cons: for a library, CI tests pinned versions your users may not have, so breakages from new releases can hide. The lockfile also needs periodic updating.
- **C. pip, version 25.1 or newer**
  - Pros: no new tool for anyone.
  - Cons: needs a recent pip, has no lockfile, and is slower.

**Recommendation: A, leaning.** `ledgerkit` is a library, and its users install whatever versions are current, so CI should too. B's strongest point is that an unexpected red CI is annoying, but that red CI is the same breakage your users would hit.

**Which install setup do you want: A (uv, no lockfile), B (uv with lockfile) or C (pip)?**

---

### Q5. What should the ruff check enforce?

**Context.** Ruff does two things. `ruff check` finds likely bugs and bad patterns (unused imports, undefined names). `ruff format --check` fails if the code's layout (spacing, quotes, line breaks) isn't in ruff's standard style. The repo has no ruff settings, so ruff uses its defaults. It already picks up the minimum Python version from `requires-python`.

**Options**
- **A. Both, with default settings**
  - Pros: catches real mistakes and ends style arguments in code review.
  - Cons: a PR fails on whitespace alone until the author runs `ruff format`.
- **B. `ruff check` only, with defaults**
  - Pros: fails only on real problems.
  - Cons: layout drifts between authors.
- **C. Either of the above, plus a `[tool.ruff]` section I'd write** (e.g., stricter rule sets)
  - Pros: you choose the strictness.
  - Cons: you'd need to tell me which rules, and stricter rules may need existing code fixed.

**Recommendation: A, firm.** The codebase is tiny, so starting with formatting enforced costs almost nothing now, and it's much harder to add later.

**Which ruff setup do you want: A (both, defaults), B (lint only) or C (with custom rules, and which ones)?**
