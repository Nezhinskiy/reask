Here are questions 2 to 5 again. What I'm building is a GitHub Actions workflow that runs on every pull request and every push to `main`. It installs `ledgerkit`, runs the linter and runs the tests. You've decided the CI service (GitHub Actions) and when it runs (PRs plus pushes to `main`). I'll write the config once you answer these four.

---

### Question 2: Which Python versions should CI test on?

**Context.** CI can run the tests once for each Python version, all at the same time. `pyproject.toml` says `requires-python = ">=3.10"`, which means anyone on 3.10 or newer can install it. Your README names two real users: billing on 3.10 and the data team on 3.13. Python 3.14 has been out since October 2025. Python 3.10 reached end of life (no more security fixes) in October 2026, but billing still uses it, so it stays.

**Options.**
- **A. Only 3.10 and 3.13**
  - Pros: it tests exactly what your two users run.
  - Cons: 3.11, 3.12 and 3.14 are allowed by `pyproject.toml` but never tested. Anyone who installs it on those versions gets untested code.
- **B. Every version from 3.10 to 3.14** (5 runs). *3.14 wasn't in my first question.*
  - Pros: it tests everything `pyproject.toml` allows. Problems on a new Python version show up before the data team upgrades.
  - Cons: each change uses 5 runs of CI time instead of 2. The runs happen side by side, so you don't wait longer.

**Recommendation.** B, leaning. CI is cheap here, and `pyproject.toml` already promises these versions. A only wins if you'd rather change `requires-python` to match what you actually support.

**Question:** Should CI test only 3.10 and 3.13, or every version from 3.10 to 3.14?

---

### Question 3: How should the tests get a Postgres database?

**Context.** `tests/test_ledger.py` uses `postgresql`, a test helper from the pytest-postgresql plugin. By default that helper starts its own temporary Postgres server for each test run. To do that, the Postgres programs must be installed on the machine running the tests. GitHub's standard Linux machines come with Postgres already installed but not running, which is exactly what this helper needs. I believe that version is 16, but I can't check GitHub's machine image from here.

**Options.**
- **A. Use the Postgres that's already on GitHub's machine; tests stay as they are**
  - Pros: no test changes, and tests run the same way on a laptop with Postgres installed.
  - Cons: GitHub picks the Postgres version, and it can change when they update their machine images.
- **B. Run Postgres in a separate container and point the tests at it**
  - Pros: you choose the exact Postgres version, such as 16 or 17, and it only changes when you change it.
  - Cons: the tests need a different helper (`postgresql_noproc`, which connects to an existing server instead of starting one). Running tests locally would then also need a Postgres server already running.

**Recommendation.** A, leaning. It needs no test changes, and the tests are still almost empty. B wins if your production Postgres version matters and you want CI to match it. If so, tell me the version.

**Question:** Should CI use the Postgres on GitHub's machine (no test changes), or a pinned Postgres container (tests change)? If you choose the container, which Postgres version?

---

### Question 4: Which tool installs the dependencies, and should versions be pinned?

**Context.** `pyproject.toml` lists the test tools (pytest, pytest-postgresql, ruff) in a newer kind of section called `[dependency-groups]`. Two tools can read it:
- **uv**, a fast Python package installer.
- **pip**, but only version 25.1 or newer.

Separately, a **lockfile** (`uv.lock`) records the exact version of every package. With it, every CI run installs the same versions. Without it, each run installs whatever is newest that day.

**Options.**
- **A. uv, with a committed lockfile**
  - Pros: fast, and every run is repeatable. A new release of a dependency can't break CI without warning.
  - Cons: `ledgerkit` is a library, and billing and the data team install the newest `psycopg`, not the pinned one. CI could pass while they hit a problem. Someone also has to update the lockfile from time to time.
- **B. uv, no lockfile**
  - Pros: CI always tests the newest versions, which is what your users get.
  - Cons: a new release of a dependency can make CI fail on a change that has nothing to do with it.
- *Also possible: pip 25.1+, no lockfile. It works, but it's slower than uv and gains you nothing here.*

**Recommendation.** A, leaning. Repeatable runs make it easier to tell "my change broke it" apart from "a dependency changed". B's argument, that CI should test what users actually get, is a fair one. It wins if you'd rather find breakage early than have stable runs.

**Question:** Should CI use uv with a committed lockfile, uv without one, or pip?

---

### Question 5: What should the linter check?

**Context.** Ruff does two separate jobs. `ruff check` finds likely bugs and bad patterns. `ruff format --check` fails CI when code isn't formatted the way ruff would format it, in the same way as the formatter Black. The repo has no ruff settings, so it would use ruff's defaults. Those defaults already read the Python version from `pyproject.toml`. The code is almost empty, so turning on either check now means nothing to fix.

**Options.**
- **A. Both checks, default settings**
  - Pros: formatting is enforced from day one, so there are no style debates in code review. Adding it later would mean one big reformatting commit.
  - Cons: contributors have to run `ruff format` before they push, or CI fails.
- **B. Bug check only, default settings**
  - Pros: less friction, since CI never fails just because of formatting.
  - Cons: formatting drifts, and enforcing it later costs a large reformatting change.

**Recommendation.** A, firm. Turning it on is free now, while there's almost no code, and expensive later. It also doesn't need any added settings.

**Question:** Should CI run both ruff checks, or only the bug check?
