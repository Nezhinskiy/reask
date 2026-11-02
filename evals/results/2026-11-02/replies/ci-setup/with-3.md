Got it: GitHub Actions, running on pull requests and on pushes to `main`. Here are the other four questions again, with more background.

**Background for all four:** I'm setting up automated checks (CI) for `ledgerkit`, a small Python library of double-entry ledger helpers. Two teams use it: billing runs Python 3.10, and the data team runs 3.13. The repo has `pyproject.toml`, a README and two tests. One test is a placeholder. The other gets a real, temporary Postgres database from the `postgresql` helper in the pytest-postgresql plugin. No source package exists yet. Nothing gets written until you answer.

---

### Q2. Which Python versions should CI test on?

**Context:** `pyproject.toml` says the library works on Python 3.10 and newer, so 3.10, 3.11, 3.12, 3.13 and the current 3.14. CI would run the tests once per version, in parallel.

**Options**
- **A. Every version from 3.10 to 3.14**
  - Pros: tests every version the package says it supports. The suite is tiny, and parallel runs add little waiting.
  - Cons: five runs instead of two. If a dependency has no 3.14 build yet, CI fails for a version neither team uses.
- **B. Only 3.10 and 3.13, the versions your two teams use**
  - Pros: covers the oldest and newest versions in real use, with fewer runs.
  - Cons: 3.11, 3.12 and 3.14 are promised but never tested. A third team on 3.12 would be relying on luck.

**Recommendation:** A, leaning. The package claims support for all of these, and testing them costs almost nothing. The best argument for B is that only two versions matter today. If a 3.14-only failure shows up, I can turn that version into a warning instead of a failure. I haven't checked that `psycopg[binary]` (the Postgres driver) publishes ready-made packages for 3.14.

**Question:** Test on every version 3.10–3.14, or only on 3.10 and 3.13?

---

### Q3. How should the tests get a Postgres database in CI?

**Context:** By default, pytest-postgresql's `postgresql` helper starts a fresh Postgres server for the test run using `pg_ctl`, Postgres's own start/stop program. So the machine running the tests needs Postgres installed. The other way is to run Postgres as a separate service that CI starts next to the tests. The plugin connects to that with a different helper, `postgresql_noproc`, which means changing the tests.

**Example:** `test_balance(postgresql)` under each option:

| | Test code | Where Postgres runs | Developer laptops |
|---|---|---|---|
| A | unchanged | started by the test itself on the CI machine | same as CI: needs Postgres installed |
| B | uses `postgresql_noproc` | a separate Postgres container (an isolated, pre-packaged copy of Postgres) started by CI | need a Postgres server already running |

**Options**
- **A. Install Postgres on the CI machine and keep the tests as they are**
  - Pros: no test changes, and tests behave the same locally and in CI.
  - Cons: CI has to locate or install the right Postgres binaries. GitHub's Ubuntu machines reportedly come with one Postgres version preinstalled but not on the PATH (I haven't verified this), so pinning a different version means installing it.
- **B. Run Postgres as a separate service and switch the tests to `postgresql_noproc`**
  - Pros: choosing the Postgres version is one line (the container image tag), and this is the common CI setup.
  - Cons: the tests have to change, and developers need a server running before tests will pass.

**Recommendation:** A, leaning. It needs no code changes, and local runs match CI. The best argument for B is that switching Postgres versions is trivial. A wins anyway because one extra install step is cheaper than changing every test and every developer's setup.

**Questions:**
- **3a.** Install Postgres on the CI machine (A), or run it as a separate service and change the tests (B)?
- **3b.** Which Postgres major version should CI use? Ideally whatever billing and the data team run in production. If you don't know, I'd use 17.

---

### Q4. How should CI install the dependencies, and should exact versions be locked?

**Context:** The dev tools (pytest, pytest-postgresql, ruff) are listed under `[dependency-groups]`, a newer `pyproject.toml` section. uv, a fast Python package installer, reads that section directly. pip only reads it from version 25.1 onward. Separately, a lockfile (`uv.lock`) records the exact version of every package, so each CI run installs exactly the same versions until someone updates the file.

**Options**
- **A. uv, with a committed `uv.lock`**
  - Pros: fast, and the same versions on every run, so CI only goes red when your code changed.
  - Cons: a library's lockfile doesn't apply to the teams that use it. When a new psycopg release breaks things, CI stays green until someone updates the lock, while billing and the data team hit the break right away.
- **B. uv, without a lockfile (always install the newest allowed versions)**
  - Pros: CI sees the same new releases your teams will get, so breakage shows up early.
  - Cons: CI can go red overnight with no code change, for example after a new pytest or ruff release.
- **C. pip 25.1 or newer**
  - Pros: no new tool for anyone.
  - Cons: slower, has no lockfile of its own, and older pip versions ignore `[dependency-groups]` without any warning.

**Recommendation:** A, leaning. It keeps CI failures tied to your own changes, and updating `uv.lock` occasionally takes care of drift. The best argument for B is that a library should be tested against what its users actually install. If you'd rather catch upstream breakage the day it happens, choose B.

**Question:** uv with a committed lockfile, uv without one, or pip?

---

### Q5. What should ruff check?

**Context:** ruff is a fast Python tool that does two jobs. The **linter** (`ruff check`) flags likely bugs, such as unused imports or undefined names. The **formatter** check (`ruff format --check`) fails CI if code isn't laid out in its standard style. There is no ruff configuration yet, so it would use its defaults. ruff reads the minimum Python version from `requires-python` on its own.

**Options**
- **A. Linter and formatter check, default settings**
  - Pros: style arguments disappear from code reviews, and nothing needs configuring.
  - Cons: CI fails on layout alone until people get used to running `ruff format` before they push.
- **B. Linter only, default settings**
  - Pros: CI only fails on probable bugs, never on layout.
  - Cons: code layout will drift.
- **C. Either of the above, plus a `[tool.ruff]` section turning on extra rules** (for example, import sorting)
  - Pros: stricter checks.
  - Cons: rules to choose and maintain before there is any code to check.

**Recommendation:** A, firm. With almost no code yet, adopting the formatter now is free, and later it costs a big reformatting change.

**Question:** Linter and formatter with defaults, linter only, or add a custom rule set?
