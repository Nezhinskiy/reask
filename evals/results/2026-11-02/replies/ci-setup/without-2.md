Got it: GitHub Actions, running on PRs and on pushes to `main`. Here are the other four in plain words. Each has a suggested answer, so you can just say "go with your picks."

**1. Which Python versions should CI test?**
Your README says billing uses 3.10 and the data team uses 3.13.
- Only those two: faster.
- Also 3.11 and 3.12: catches problems in between.

*My pick: just 3.10 and 3.13.*

**2. How should the tests get a database?**
One test needs a running Postgres database.
- **Option A:** CI installs Postgres and the test starts its own database, like it does on your laptop. No test changes.
- **Option B:** GitHub runs a database next to the tests, and I make a small change so the test connects to it.

Also, which Postgres version do you use in production, if you know?

*My pick: Option A, with Postgres 17 unless you tell me otherwise.*

**3. Which tool should install the dependencies?**
- **uv**: a fast installer that reads your dev tool list as written.
- **pip**: works too, but needs a recent version.

If uv, I can also commit a lock file that pins exact versions, so CI doesn't break when a library releases an update.

*My pick: uv, with the lock file.*

**4. How strict should the code-style check be?**
- **Lint only**: catches likely bugs and unused imports.
- **Lint plus formatting**: also fails if code isn't formatted the standard way.

*My pick: both, with default settings.*
