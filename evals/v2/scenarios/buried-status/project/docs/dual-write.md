# Dual-write (MIG-21, PR #88)

#88 merged 2026-10-27 and shipped in release 4.12. Since then every order that is created or
edited writes `total_minor` next to `total_text`, in the same transaction.

- Spot check 2026-10-29: 1,200 orders created since 4.12, all with `total_minor` equal to the
  parsed `total_text`.
- Refunds edit old orders, so a few thousand pre-4.12 rows already have `total_minor`; the
  backfill skips any row where it is set.
