Got it: GitHub Actions, running on PRs and on pushes to `main`. Here are the other four in plain words, each with what I'd pick:

**1. Which Python versions should CI test on?**
Billing uses 3.10 and the data team uses 3.13. I can test just those two, or also 3.11 and 3.12 in between. Testing all four costs a bit more CI time.
→ I'd test all four.

**2. How should the database tests get a database?**
`test_ledger.py` needs a real PostgreSQL database. There are two ways to give it one:
- **Install PostgreSQL on the CI machine.** The tests stay exactly as they are.
- **Run PostgreSQL as a separate helper container.** This is the more common CI setup, but I'd have to change a few lines in the tests.

Also, which PostgreSQL version does production use (e.g., 16 or 17)?
→ I'd install it on the CI machine so the tests don't change. If you're not sure of the version, I'd use whatever production runs, or 17.

**3. Can I use the tool `uv` to install dependencies?**
Your `pyproject.toml` lists dev tools in a format that uv handles directly. Plain `pip` handles it too, but only in recent versions.
→ I'd use uv. Do you also want me to add a lock file, which pins exact package versions so every CI run installs the same thing?

**4. How strict should the code-style check (ruff) be?**
- **Bug check only:** catches likely bugs and bad patterns.
- **Bug check plus formatting:** also fails if code isn't formatted the standard way.

→ I'd do both, with ruff's default rules. A one-time format pass might change some files.

You can answer with something like "1: all four, 2: install, 17, 3: yes + lock, 4: both", or just "go with your picks."
