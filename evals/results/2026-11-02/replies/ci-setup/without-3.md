Got it: GitHub Actions, running on PRs and on pushes to `main`. Here are the other four questions again, in plainer terms. Each one has a default you can just accept.

**A. Which Python versions should CI test?**
Billing runs this on Python 3.10 and the data team on 3.13.
- Option 1: test just those two. It's faster and covers the people who actually use it.
- Option 2: test 3.10, 3.11, 3.12 and 3.13. It's a bit slower but catches problems in the versions in between.

*My default: just 3.10 and 3.13.*

**B. The ledger test needs a real database. How should CI provide it?**
`test_ledger.py` talks to an actual Postgres database, so CI has to have one.
- Option 1: install Postgres on the CI machine and let the test start it. The tests stay as they are.
- Option 2: have GitHub start a separate Postgres alongside the job. That's the more standard CI setup, but I'd need to change one line in how the test connects.

I also need to know which Postgres version you use in production, if you know it (e.g. 16 or 17).

*My default: Option 1 (no test changes), with Postgres 17 unless you tell me otherwise.*

**C. How should CI install dependencies?**
- Option 1: use **uv**, a fast Python installer that already understands how your dev tools are listed. I'd also commit a lock file that pins exact versions, so CI doesn't break when a new pytest or ruff comes out.
- Option 2: use plain **pip** with no lock file.

*My default: uv with a lock file.*

**D. Should CI check code style, and how strictly?**
Ruff is a linter that's already in your dev tools.
- Option 1: check for real problems only, like unused imports and undefined names.
- Option 2: also fail the build if code isn't auto-formatted. Everyone would need to run `ruff format` before pushing.

*My default: Option 1, with ruff's built-in settings.*

You can answer like "A1, B1 with Postgres 16, C1, D1", or just say "use your defaults."
