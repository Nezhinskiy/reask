# deploy/

- `crontab` is a copy of nightjar's entry in the ops team's `ops-schedules` repository, which is
  what the hosts actually run. A nightly sync job overwrites this copy at 02:00 UTC, so an edit
  made here is lost the next night and never reaches the hosts. To change a schedule, file an OPS
  ticket; ops apply schedule changes in their weekly change window on Wednesdays.
- `tests/test_crontab.py` (the `deploy-smoke` check in CI) parses every line of `crontab` against
  the CLI on the branch, so a CLI change that would break a scheduled command fails CI.
