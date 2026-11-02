Got it: GitHub Actions, running on pull requests and on pushes to `main`. Here are the other four questions in plainer terms, each with what I'd pick if you don't mind either way:

**1. Which Python versions should CI test?**
Your README says one team uses Python 3.10 and another uses 3.13. I can test just those two, or also the versions in between (3.11 and 3.12). Testing more versions makes CI a bit slower but catches more problems.
*My pick: just 3.10 and 3.13.*

**2. How should the tests get a database?**
One test needs a real Postgres database. There are two ways to provide it:
- **Keep the tests as they are.** CI installs Postgres on the test machine, and the test starts its own database.
- **Change the tests a little.** CI runs a separate database alongside the tests, and the test connects to it. This is the more common setup, but I'd have to edit the test file.

Also, which Postgres version do you use in production, if you know?
*My pick: keep the tests as they are, with the same Postgres version as production.*

**3. Which tool should install the dependencies?**
The way your dev tools (pytest, ruff) are listed works best with a tool called **uv**. Plain **pip** can also handle it, but only recent versions. With uv, I can also add a "lock file" that pins exact package versions. That way CI doesn't break when some library releases an update.
*My pick: uv, with a lock file.*

**4. How strict should the code-style checks be?**
Ruff is already in your dev tools. It can:
- only flag likely bugs and sloppy code, or
- also fail CI when code isn't formatted in its standard style.

Right now it uses its default rules. I can leave those or set your own.
*My pick: both checks, default rules.*

You can reply with something like "your picks, Postgres 16", or change any of them.
