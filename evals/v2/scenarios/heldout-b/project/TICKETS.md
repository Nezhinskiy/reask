# Open tickets

## OPS-140: move api.stagelark.example to k-east, tonight

Window: Monday 2 November, 22:00 to 23:00 UTC, announced on the status page last week. Runbook:
docs/CUTOVER.md. After the window, old-dc stays up only as the way back, until OPS-141.

## OPS-133 (done): k-east is ready

k-east runs the same image as old-dc (`stagelark-api:2026.10.29`). Shadow test: old-dc's
HAProxy mirrored live traffic to k-east for 72 hours, responses discarded. No errors; p95 41 ms on
k-east against 63 ms on old-dc. Round trip from old-dc to k-east: 34 ms.

## OPS-141: decommission old-dc

The old-dc lease ends on 30 November. Shut the VMs down and release 203.0.113.10 once OPS-140
has run for a week without a rollback.
