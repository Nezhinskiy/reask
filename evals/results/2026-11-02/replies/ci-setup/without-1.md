Got it: GitHub Actions, running on PRs and on pushes to `main`. Here are the other four in plainer terms. Each has a default I'd pick, so "yes to all defaults" is a fine answer.

**1. Which Python versions should CI test?**
Your README says billing uses Python 3.10 and the data team uses 3.13. CI can run the tests on each version you name. I can test just those two, or also the versions in between (3.11 and 3.12). Testing more versions makes each run a bit slower.
**Default:** just 3.10 and 3.13.

**2. How should the database test get a database?**
`tests/test_ledger.py` needs a real PostgreSQL database while it runs, and CI machines don't come with one. There are two ways to provide it:
- **A:** I install PostgreSQL on the CI machine and the test starts it itself. Your test code stays exactly as it is.
- **B:** CI starts a database next to the tests and the test connects to it. This is a bit more standard for CI, but I'd have to change a line in your test.

**Default:** A, so your tests don't change.

Also, which PostgreSQL version do you run in production? If you don't know, I'll use 17, the current one.

**3. How should CI install your project's tools?**
Your `pyproject.toml` lists tools like pytest in a way that a tool called **uv** reads directly. The usual `pip` can only read it in recent versions. I'd use uv. It's fast and widely used, and you don't need to install it yourself.

A related question is whether to pin exact versions. uv can create a `uv.lock` file that records the exact version of every package. With it, CI installs the same versions every time. Without it, CI gets the newest allowed versions, so a run can break when a package releases an update.
**Default:** use uv, and add `uv.lock`.

**4. How strict should the code-style checks be?**
Your project includes **ruff**, a tool that checks Python code. CI can run it in two ways:
- **Problems only:** it flags things like unused imports and likely bugs.
- **Problems and formatting:** it also fails if the code isn't formatted in ruff's standard style (spacing, line breaks, quotes).

**Default:** both, with ruff's standard settings. If you choose both, I'll first run the formatter once on the existing code so CI doesn't fail on day one.

Answer whichever you like, or say "defaults", and then I'll write the config.
