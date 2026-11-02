# Backfill runbook (MIG-21)

- One wave per run: `python backfill_totals.py --years 2023`. A wave can be split by month
  (`--months 2024-01..2024-06`). The script is idempotent: it skips rows that already have
  `total_minor`, so a stopped run can be restarted.
- Default slot: the night window 22:00-04:00, when order traffic is lowest.
- Daytime runs are allowed with `--throttle-ms 50`, and only after the DB on-call agrees.
  Throttled, the script does about 100,000 rows an hour.
- Batch size stays at 5,000 rows or below. In the staging dry run, 20,000-row batches kept the
  read replica up to 4 minutes behind the primary; the invoice API reads from the replica, so
  customers were shown invoices with stale totals.
- After each wave, run `verify_totals --wave <W>`. Rows whose `total_text` is 'N/A' (cancelled
  test orders from the old shop) cannot be parsed: leave `total_minor` NULL and note the count.
  Anything else that fails to parse or mismatches stops the next wave.
