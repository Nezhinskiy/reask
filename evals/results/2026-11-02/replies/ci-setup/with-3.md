Decided so far: **GitHub Actions**, running on every pull request and on every push to `main`.

**What we're building:** a GitHub Actions workflow for `ledgerkit`, a small Python library of double-entry ledger helpers. On every PR and every push to `main` it installs the library, checks the code style, and runs the tests. A red ✗ on a PR means something broke before it gets merged. The repo has `pyproject.toml`, a README and two test files. Both tests are placeholders, and there's no library source code yet. Four answers decide what the workflow file contains.

---

### 1. Which Python versions should CI test?

**Context:** CI can run the same tests on several Python versions in parallel. Each version adds one more check on the PR, a minute or two each, and costs nothing on public repos. `pyproject.toml` says the library supports Python 3.10 and newer. The README names two users: billing on 3.10 and the data team on 3.13. The newest Python releases are 3.14 and 3.15 (3.15 came out in October 2026), and 3.10 itself reaches end of life around now.

**Options:**
- **A. 3.10 and 3.13**
  - Pros: tests exactly what your two real users run.
  - Cons: someone on 3.11, 3.12 or 3.14 could hit a break that CI never saw.
- **B. Every version from 3.10 to 3.13**
  - Pros: covers every version in between.
  - Cons: doubles the number of checks, and the in-between versions almost never break on their own.
- **C. (new) 3.10, 3.13 and the newest Python**
  - Pros: warns you early about the version the data team will move to next.
  - Cons: the database driver (psycopg) may not have ready-made packages for 3.15 yet, so CI could fail for reasons that aren't your code.

**Recommendation:** A, leaning. The two ends of the range catch nearly all breaks. The best argument against it is that "3.10 and newer" invites other users, but the README lists only two.

**Question:** Should CI test 3.10 + 3.13, every version from 3.10 to 3.13, or 3.10 + 3.13 + the newest?

---

### 2. How should CI get a database for the tests?

**Context:** `tests/test_ledger.py` uses `postgresql`, a ready-made test helper from the pytest-postgresql plugin. It starts its own temporary PostgreSQL server for the test and shuts it down afterwards. To do that, the PostgreSQL programs have to be installed on the CI machine.

**Options:**
- **A. Install PostgreSQL on the CI machine and leave the tests unchanged**
  - Pros: tests run the same way on a laptop and in CI.
  - Cons: the workflow needs an install step and has to point the plugin at the server programs, which aren't on the default path.
- **B. Run PostgreSQL alongside the job as a separate container (a "service") and switch the test to the plugin's `postgresql_noproc` helper, which connects to a server that's already running**
  - Pros: picking the PostgreSQL version is a one-line change in the workflow.
  - Cons: you'd have to change the tests, and on a laptop you'd then need to start a database yourself before running them.

**Unchecked fact:** GitHub's standard Ubuntu machines are documented as shipping with one PostgreSQL version preinstalled. If that holds, option A needs no install step for that version. I can't verify it from here.

**Recommendation:** A, leaning. It keeps the tests as written. The best argument for B is easy version pinning, but A can install a specific version too.

**Question:** A or B? And which PostgreSQL version do billing and the data team run in production? CI should test against that version.

---

### 3. How should CI install the library and its tools?

**Context:** The dev tools (pytest, its PostgreSQL plugin and ruff) are listed in a newer section of `pyproject.toml` called `[dependency-groups]`. The fast installer **uv** reads that section directly. **pip** reads it only from version 25.1 on. A **lockfile** (`uv.lock`) records the exact version of every package. With one, every CI run installs the same versions. Without one, each run installs the latest allowed versions. Your users never see the lockfile: billing and the data team always get the latest psycopg that `pyproject.toml` allows.

**Options:**
- **A. uv, no lockfile**
  - Pros: CI tests the same package versions your users will actually install.
  - Cons: a new release of a package can turn CI red overnight even though your code didn't change.
- **B. uv with a committed lockfile**
  - Pros: runs are repeatable, and a failure always comes from a change in your code.
  - Cons: you test old pinned versions while your users run newer ones, and you have to update the lockfile by hand.
- **C. pip 25.1+**
  - Pros: no new tool to learn.
  - Cons: installs more slowly, and installing the dev tools takes an extra flag.

**Recommendation:** A, leaning. For a library, testing what users will actually get matters more than repeatable runs. The best argument for B is that surprise failures are annoying, but they also warn you about a break before billing hits it.

**Question:** uv without a lockfile, uv with one, or pip?

---

### 4. Which style checks should CI run?

**Context:** ruff is the style tool already in your dev list. It has two parts. `ruff check` catches likely bugs and sloppy code, such as unused imports. `ruff format --check` fails CI if code isn't laid out the standard way (the fix is to run `ruff format`). With no settings file, ruff uses its built-in defaults, which already respect "Python 3.10 and newer".

**Options:**
- **A. Both checks, default settings**
  - Pros: there's almost no code yet, so enforcing formatting now causes no cleanup work.
  - Cons: contributors' PRs fail until they run the formatter.
- **B. `ruff check` only**
  - Pros: CI fails only on real problems, never on layout.
  - Cons: code layout drifts between contributors.
- **C. Both checks, plus a ruff settings section that turns on stricter rules**
  - Pros: catches more.
  - Cons: you'd have to choose which rules, which is a decision of its own.

**Recommendation:** A, firm. The codebase is empty, so turning formatting on now costs nothing, and adding it later means one big reformatting commit.

**Question:** Both checks with default settings, `ruff check` only, or stricter rules?
