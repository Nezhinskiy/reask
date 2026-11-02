# Child report: #12 extract config (finished 2026-10-30 16:40)

Done:
- Moved settings parsing from `nightjar/cli.py` into `nightjar/config.py` (`load_settings()`).
- `cli.py` now calls `config.load_settings()`; no behaviour change.
- Added `tests/test_config.py` (6 tests). Full suite: 41 passed.

Open: nothing. Ready to merge.
