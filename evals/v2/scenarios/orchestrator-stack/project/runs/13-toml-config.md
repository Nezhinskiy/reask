# Child report: #13 TOML config (finished 2026-10-31 11:05)

Done:
- `config.load_settings()` reads `nightjar.toml` with `tomllib`. Same keys as before; the `[mail]`
  section is now `[smtp]`.
- Removed the `configparser` path that read `nightjar.ini`.
- Added `docs/migrating-to-toml.md` with an old-key to new-key table.
- Full suite: 44 passed.

Needs a decision (not mine to make):
- A host that still has only `nightjar.ini` now starts with defaults: no SMTP host, so
  `send-digest` runs, logs "0 recipients" and sends nothing, with no error. Two ways out:
  1. keep reading `nightjar.ini` as a fallback for one release, with a deprecation warning
     (about 40 lines; the INI parser comes back);
  2. refuse to start, with an error that names `nightjar.ini` and points to
     `docs/migrating-to-toml.md` (about 8 lines).
  I left the behaviour as it is until someone decides.
