# Child report: #14 drop --legacy-paths (finished 2026-10-31 15:20)

Done:
- Removed the `--legacy-paths` flag and the code behind it (looking for data under
  `~/.nightjar/`). Data is now only read from `$XDG_DATA_HOME/nightjar`, where every host has
  kept it since 1.6.
- Unit tests: 43 passed locally.
- Did not run the deploy checks: they need the `deploy/` directory, which my sandbox did not have.

Open: none known.
