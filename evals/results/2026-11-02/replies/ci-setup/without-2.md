Got it: GitHub Actions, running on PRs and on pushes to `main`. Here are the other four in plainer terms, each with a default you can just accept.

**1. Which Python versions should CI test?**
Your README says billing uses Python 3.10 and the data team uses 3.13. CI can run the tests once per version. Should it be:
- **(a)** just 3.10 and 3.13 (faster), or
- **(b)** every version from 3.10 to 3.13 (also catches problems in the versions between)?

I'd go with (b). It costs little and nothing slips through.

**2. Database for the tests.**
`test_ledger.py` needs a real Postgres database to run against. I can provide one in CI in one of two ways:
- **(a)** Install Postgres on the CI machine. Your test files don't change.
- **(b)** Run Postgres as a separate container next to the tests. This is the more common CI setup, but I'd have to change a line in your tests so they connect to it.

I'd go with (a) so your tests stay as they are. Also, which Postgres version do you use in production? If you're not sure, I'll pick 17, the latest.

**3. Tool for installing dependencies.**
Your `pyproject.toml` lists the test tools (pytest, ruff) in a format that **uv**, a newer and faster Python package installer, supports directly. Plain pip needs a recent version and extra flags. Can CI use uv?

If yes, I'd also add a **lockfile** (`uv.lock`). It records the exact version of every dependency, so CI installs the same thing every time. Without it, a new release of a dependency can break CI even when your code hasn't changed. I'd use uv and add the lockfile.

**4. Code style checks.**
Ruff is already in your dev tools. In CI it can:
- **(a)** check only for likely bugs and mistakes (unused imports, undefined names, etc.), or
- **(b)** also fail the build if code isn't formatted in ruff's standard style.

(b) keeps formatting consistent, but anyone pushing code would need to run `ruff format` first. I'd go with (b) unless that would bother your team. Either way I'd use ruff's default rules and not add custom settings.

If you're happy with my picks, reply "go with your picks" (and give a Postgres version if you know it). I'll wait for your answer before writing anything.
