Here are the four open questions again, in plain words.

**What we're building:** a GitHub Actions workflow for `ledgerkit`, a small Python library of double-entry bookkeeping helpers. It runs whenever someone opens or updates a pull request and whenever someone pushes to `main`. It installs the library, runs a lint check, and runs the tests. I haven't written anything yet; the workflow file depends on these four answers.

**Decided:** GitHub Actions; runs on PRs and pushes to `main`.

**What's in the repo:** a `pyproject.toml` (Python 3.10 or newer, one dependency `psycopg`, which is the Postgres driver) and two test files. There's no source code folder yet. One test (`test_balance`) needs a real running Postgres database. The README says two teams use the library: billing on Python 3.10 and the data team on Python 3.13.

---

### Question 1: Which Python versions should CI test?

**Context:** CI runs the tests once per Python version, in parallel. `pyproject.toml` says the library works on 3.10 and anything newer. In practice, only 3.10 and 3.13 are actually used.

**Options:**
- **A. Only 3.10 and 3.13.** These are the versions the two teams use.
  - Pros: tests exactly what's in production; two jobs per run.
  - Cons: `pyproject.toml` promises 3.11 and 3.12 too, and nothing would check that promise.
- **B. Every version: 3.10, 3.11, 3.12, 3.13.**
  - Pros: checks every version the package says it supports.
  - Cons: twice the jobs, for versions nobody uses today. A break on 3.11 or 3.12 that 3.10 and 3.13 both miss is rare.

**Recommendation:** A, leaning. The strongest case for B is that it's cheap, and `pyproject.toml` makes the promise. But no user is on 3.11 or 3.12, and the two ends of the range catch almost everything. B would win if you expect new users on 3.11 or 3.12.

**Question:** Should CI test only 3.10 and 3.13, or all of 3.10 to 3.13?

---

### Question 2: How should the tests get a Postgres database?

**Context:** `test_balance` uses a ready-made helper ("fixture") from the `pytest-postgresql` plugin. By default, that helper starts its own temporary Postgres server for each test run. To do that, it needs the Postgres programs installed on the machine. The other choice is to have GitHub start a Postgres server alongside the job and point the tests at it. That needs a different helper, so the test code changes.

**Options:**
- **A. Use the Postgres already on GitHub's machine; tests stay as they are.** GitHub's standard Ubuntu machines come with Postgres installed. The only extra step is telling the plugin where it is.
  - Pros: no test code changes; CI runs the tests exactly the way a developer does locally.
  - Cons: you're tied to the Postgres version GitHub ships (16 on current images). Testing a different version means an extra install step.
- **B. GitHub runs Postgres separately (a "service container"), and the tests connect to it.**
  - Pros: any Postgres version you want, chosen with one line.
  - Cons: the tests have to change to use the plugin's "connect to an existing server" helper. Then every developer also needs a running Postgres server locally, not just the Postgres programs installed.

**Recommendation:** A, leaning, if your production Postgres is 16. It's the only option that leaves the tests alone. One thing I haven't checked: I'm going on what GitHub's Ubuntu machines usually ship (Postgres 16); I can't see that from here. If your production databases run another version, say 15 or 17, B becomes the better fit.

**Question:** Which way should the tests get Postgres (A or B)? And which Postgres version do billing and the data team run in production?

---

### Question 3: Which tool installs the dependencies, and should exact versions be locked?

**Context:** `pyproject.toml` lists the test tools (pytest, the Postgres plugin, ruff) in a fairly new format called "dependency groups". `uv` (a fast Python installer) supports it fully. Plain `pip` supports it only from version 25.1, and only with an extra flag. Separately, a lockfile (`uv.lock`) records the exact version of every dependency, so every CI run installs the same thing.

**Options:**
- **A. uv, with a committed lockfile.**
  - Pros: every CI run installs identical versions, so a red build means your code changed, not a dependency.
  - Cons: billing and the data team don't use your lockfile; they get whatever is newest. CI can stay green while their fresh installs break. Someone also has to update the lockfile now and then.
- **B. uv, no lockfile.**
  - Pros: CI always tests against the newest dependency versions, like your users get.
  - Cons: a new release of psycopg or pytest can turn CI red on a PR that didn't touch anything related.
- **C. Plain pip, version 25.1 or newer.**
  - Pros: no new tool.
  - Cons: slower, and the dependency-groups format only works with a fairly recent pip.

**Recommendation:** A, leaning. The strongest case against it is B's: this is a library, and users get the newest versions. But a CI that goes red for reasons unrelated to the change gets ignored quickly. B would win if you'd rather hear about dependency breakage immediately, even when it isn't your bug.

**Question:** Should CI install with uv and a committed lockfile, uv without a lockfile, or plain pip?

---

### Question 4: How strict should the style check be?

**Context:** `ruff` is a code checker that's already in the test tools. It can do two separate things: `ruff check` finds likely bugs and sloppy code (unused imports, undefined names), and `ruff format --check` fails the build if code isn't formatted in ruff's standard style. The repo has no ruff settings, so ruff uses its defaults. It already reads the minimum Python version from `pyproject.toml`.

**Options:**
- **A. Both `check` and `format --check`, default settings.**
  - Pros: consistent formatting from day one. With only two small test files, adopting it now costs nothing.
  - Cons: contributors have to run `ruff format` before pushing, or CI fails over whitespace.
- **B. `check` only.**
  - Pros: CI fails only on real problems, never on style.
  - Cons: formatting drifts. Turning it on later means one big reformatting commit.

**Recommendation:** A, firm. The codebase is nearly empty, so there's no reformatting to do. Default settings are fine; I'd add ruff settings only if you have a house style.

**Question:** Should CI run both checks, or `ruff check` only?
