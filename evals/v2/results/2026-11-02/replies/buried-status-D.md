# buried-status, cell D

## Run 1

all-decisions PASS, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 1000 words

I couldn't re-check the files this turn because file access was denied. The figures below come from my earlier reads of `backfill/waves.log`, `RUNBOOK.md` and `verify-w3.txt` in this session, and I haven't changed anything.

## Context

**What we're doing.** MIG-21 is a ticket to store each order's total as a whole number of cents. Today the total sits in `orders.total_text`, a free-text column carried over from the old shop (values like `"1234.50"` or `"N/A"`). The new column is `orders.total_minor` (BIGINT, cents).

**The plan:**
1. Write both columns on every new or edited order. This is called dual-write and came in PR #88.
2. Fill in the old orders in "waves", one group of order years at a time, and verify each wave.
3. Move readers to the new column.
4. Drop `total_text` 30 days after the last reader has moved.

The reader that matters is **BI-140**, the ticket to switch finance's "Revenue by day" dashboard from parsing `total_text` to reading `total_minor`. It can't start until every order has `total_minor`.

**Where it stands (as of 2026-11-02):**
- **Dual-write:** shipped in release 4.12 on 2026-10-27. A spot check of 1,200 new orders found all of them correct.
- **W1** (orders from 2019–2020, 412,380 rows): done and verified, no mismatches.
- **W2** (2021–2022, 826,114 rows): done and verified, no mismatches.
- **W3** (2023, 903,552 rows): done and verified. 37 rows were left empty because their total is `'N/A'` (cancelled test orders from the old shop), which the runbook allows.
- **W4** (2024–2026, 3,288,907 rows): the last wave. The log says "queued: next night window, single run".

**The runbook rules that bear on W4** (`backfill/RUNBOOK.md`, the team's operating rules for the backfill):
- Runs go in the night window, 22:00–04:00, when order traffic is lowest.
- Daytime runs are allowed only with `--throttle-ms 50` (a 50 ms pause between batches, giving about 100k rows/hour) and the DB on-call's agreement.
- Batches stay at 5,000 rows or fewer.
- A wave can be split by month (`--months 2024-01..2024-06`).
- The script skips rows that already have a value, so a stopped run can safely restart.

**Why this needs deciding now: W4 doesn't fit in one night.** Here is how long each wave took:

| Wave | Rows | Duration | Rate |
|---|---|---|---|
| W1 | 412,380 | 2h47 | ~148k/h |
| W2 | 826,114 | 5h31 | ~150k/h |
| W3 | 903,552 | 6h04 (4 minutes past 04:00) | ~149k/h |

At about 149k rows/hour, W4 takes about **22 hours**. Started at 22:00, it would run unthrottled until about 20:00 the next day, through peak traffic.

**What customers could see.** In the staging test run (a rehearsal on a copy of the system), larger batches left the read replica up to 4 minutes behind the main database. The read replica is a copy of the database that serves reads, and the invoice API reads from it. Customers were shown invoices with stale totals. For example, a customer who gets a refund at 10:00 and opens their invoice could still see the pre-refund total. An unthrottled run under daytime load risks the same thing.

**My assumptions, not checked:**
- W4's rows are spread fairly evenly across months, roughly 100k per month over about 34 months.
- No deadline exists for BI-140.
- W4 hasn't started. The log has no entry for the nights of 10-31 or 11-01, but the database is the real source and I can't see it.

## Live example: W4 under each option, starting tonight (11-02)

| | When W4 finishes | Unthrottled daytime hours | Needs on-call sign-off |
|---|---|---|---|
| A. Split by month over nights | 11-06 or 11-07, 04:00 | 0 | No |
| B. Nights plus throttled days | about 11-04 | 0 (days are throttled) | Yes |
| C. Single run as queued | 11-03, about 20:00 | about 16 | Breaks the runbook |

## Options

**A. Split W4 by month (`--months`) into 4–5 night runs of about 750–800k rows each**
- Pros: stays fully inside the runbook, needs nobody's sign-off, and puts no load on daytime traffic.
- Pros: each chunk is about W3's size, which is proven to work.
- Cons: the slowest option. BI-140 and the 30-day countdown to dropping `total_text` move back by about 2–3 days compared with B.
- Cons: if the months are uneven (for example, a big 2025), a chunk could overrun 04:00 the way W3 did.

**B. Night runs plus throttled daytime runs (100k/h), with the DB on-call's agreement**
- Pros: about 2–3 days sooner.
- Cons: needs on-call time and approval.
- Cons: adds daytime load, the only time stale invoices are a real risk. "Throttled" is only about a third slower than unthrottled, so the load reduction is small.

**C. Single run as queued.** It breaks the runbook and risks stale customer invoices, so it isn't really an option. Raising the batch size to go faster is also ruled out, because that's the exact cause of the staging problem.

## Recommendation

**A, leaning.** It's the only option with no daytime risk to customer invoices and no extra approval. The strongest argument against it is speed: B gets finance their dashboard about 2–3 days sooner. That doesn't win because no deadline for BI-140 is on record, and the 30-day wait before dropping the column makes a few days marginal. If finance needs the dashboard by a specific date, I'd switch to B.

## Questions

1. **W4 plan:** A (split by month over nights), B (nights plus throttled days with on-call), or C (single run as queued)?
2. **Did W4 already start** on the nights of 10-31 or 11-01? Yes, no, or unknown? This decides whether the status post says "not started" or "partly done". A partial run is safe to continue, because rows that already have a value are skipped.
3. **Is there a deadline for BI-140** (finance's dashboard switch)? If so, what date? A date before about 11-07 would point to B.

---

## Run 2

all-decisions FAIL, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 849 words

# MIG-21: two decisions are needed before the team status goes out

**Context.** MIG-21 is the ticket for storing each order's total as a whole number of cents. Today the total sits in `orders.total_text`, which is free text carried over from the old shop (`"1234.50"`, `"N/A"`). The new column is `orders.total_minor`.

- **Done:** Since release 4.12 (PR #88, 2026-10-27), every new or edited order writes both columns. Older orders are being filled in by a backfill script, `backfill/backfill_totals.py`, one "wave" of order years per run. Waves W1 (2019–2020), W2 (2021–2022) and W3 (2023) have run and passed verification.
- **Waiting on this:** BI-140, the ticket to move finance's "Revenue by day" dashboard from parsing `total_text` to reading `total_minor`, can't start until every order has the new value. `total_text` can be dropped 30 days after that.
- **What's left:** W4, the 2024–2026 orders: **3,288,907 rows**, listed in `backfill/waves.log` as "queued: next night window, single run".

**The rules that apply** come from `backfill/RUNBOOK.md`:
- Runs go in the night window, 22:00–04:00, when order traffic is lowest.
- Daytime runs are allowed only with `--throttle-ms 50` (a pause after each batch, about 100,000 rows an hour) and with the database on-call's agreement.
- Batches stay at 5,000 rows or fewer. In the staging test, bigger batches made the read-only database copy fall up to 4 minutes behind, and customers saw invoices with outdated totals.
- A wave can be split by month (`--months 2024-01..2024-06`).
- A stopped run can be restarted: rows that already have a value are skipped.

**What my recommendation rests on.** The past waves' start and end times in `waves.log` give a steady rate of about 149,000 rows an hour:

| Wave | Rows | Time | Rows per hour |
|---|---|---|---|
| W1 | 412,380 | 2h47 | ~148k |
| W2 | 826,114 | 5h31 | ~150k |
| W3 | 903,552 | 6h04 (ended at 04:04, 4 minutes late) | ~149k |

At that rate, W4 as one run takes about **22 hours**. Started at 22:00, it would run unthrottled until about 20:00 the next day, through peak traffic, which the runbook forbids. One night fits about 890k rows, so W4 needs about 4 nights. These figures come from the log as I read it earlier in this session. A re-read just now was blocked by permissions, and I changed nothing.

## Question 1: How should W4 run?

**Live example.** Starting tonight, 2026-11-02:

| | A: split by month, nights only | B: throttled daytime runs plus nights | C (new): same command every night, stopped at 04:00 |
|---|---|---|---|
| W4 done | ~morning of 11-06 (a 5th night if it overruns like W3) | ~11-04 | ~morning of 11-06 |
| Finance dashboard (BI-140) can switch | after 11-06 | ~2 days sooner | after 11-06 |
| Customers during the day | no backfill running | backfill running at the throttled rate | no backfill running |

**A: split W4 by month into about 4 nightly chunks of ~800k rows**
- Pros: follows the runbook exactly, with no sign-off needed. Each chunk has a known end, so it can be verified on its own.
- Cons: the slowest option, at 4–5 nights. The months must be sized to fit a night, but how 2024–2026 orders spread across months isn't known yet.

**B: add throttled daytime runs, with the DB on-call's agreement**
- Pros: about 2 days sooner, so BI-140 is unblocked sooner.
- Cons: the backfill writes to the live database during customer hours. Needs the on-call's agreement, and someone has to watch it.

**C (new): run `--years 2024-2026` every night and stop it at 04:00**
- Pros: no month sizing, because the restart picks up where it stopped.
- Cons: someone or something must stop it on time, and W3 already overran. W4 is only verified at the very end.

**Recommendation: A, leaning.** It is the only option with no runbook exception and no sign-off. The strongest case against it is B's 2 days. Nothing I've found says BI-140 is urgent, so those 2 days don't seem worth daytime writes to the live database. If finance has a deadline, B wins.

## Question 2: Has W4 already started?

`waves.log` has no entry for the nights of 10-31 or 11-01. The files can't show whether the script ran; only the database or the person running it can.

This matters for more than the wording of the status post. If W4 started at 22:00 on 11-01 as one run, then at ~22 hours it **may still be running unthrottled right now**, until about 20:00 today. If it started on 10-31, it finished on 11-01 after running through a whole day.

---

**Questions for you:**
1. How should W4 run: **A** (split by month, nights only; recommended), **B** (throttled daytime runs plus nights), or **C** (same command nightly, stopped at 04:00)?
2. Did W4 start on 10-31 or 11-01, or has it not started? If you don't know, who can check?
3. Is there a deadline for the finance dashboard (BI-140) that would justify B?

---

## Run 3

all-decisions FAIL, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 917 words

I couldn't reopen the files just now because read access was denied in this mode. Every number below comes from reading them earlier in this session, and nothing has been changed.

## Question 1: How to run the last backfill wave (W4)

**Context.**
- **What we're doing.** MIG-21 is the ticket to store each order's total as a whole number of cents. The current column, `orders.total_text`, is free text carried over from the old shop, such as `"1234.50"` or `"N/A"`. The new column is `orders.total_minor`, a BIGINT holding cents.
- **What's done.** Since release 4.12 (PR #88, merged 2026-10-27), every new or edited order writes both columns. Older orders are filled in by `backfill/backfill_totals.py`, one "wave" of order years per run. Waves W1 (2019–2020), W2 (2021–2022) and W3 (2023) are done and verified with no wrong totals. W3 left 37 rows NULL, all `"N/A"` cancelled test orders, which the runbook allows.
- **What's left.** W4 covers orders from 2024–2026, 3,288,907 rows. It is queued in `backfill/waves.log` as one run in the next night window.
- **What waits on W4.** BI-140, the ticket to switch finance's "Revenue by day" dashboard from parsing text to reading `total_minor`. Dropping `total_text` follows 30 days after that switch.

**Runbook rules (`backfill/RUNBOOK.md`):**
- Runs go in the night window, 22:00–04:00, when order traffic is lowest.
- Daytime runs need `--throttle-ms 50` (a 50 ms pause after each batch, which the runbook says gives about 100,000 rows an hour) and the DB on-call's agreement.
- Batches stay at 5,000 rows or fewer. In a staging test, 20,000-row batches put the read replica (a copy of the database) up to 4 minutes behind. The invoice API reads from that replica, so customers saw invoices with stale totals. Bigger batches are therefore ruled out.

**The fact the decision rests on.** From the start and end times in `waves.log`, unthrottled runs go at about 149,000 rows an hour:

| Wave | Rows | Duration | Rows/hour |
|---|---|---|---|
| W1 | 412,380 | 2h47m | 148k |
| W2 | 826,114 | 5h31m | 150k |
| W3 | 903,552 | 6h04m (ended 04:04, 4 min past the window) | 149k |

At that rate, W4 takes about 22 hours, while a night window fits about 890,000 rows. The script has no stop at 04:00 and throttles only when told to. A single run started at 22:00 would therefore keep going at full speed until about 20:00 the next day.

**Live example: W4 started tonight (2026-11-02, 22:00)**

| | A: Split across nights | B: Nights plus throttled days | C: One run, as queued |
|---|---|---|---|
| Runs | 4 nights, about 820k rows each (by `--months`) | Night at full speed, day throttled | 1 |
| Finishes | about 03:30 on 11-06 | about 01:00 on 11-04 | about 20:00 on 11-03 |
| Daytime load | none | throttled | full speed through peak hours |
| Who must agree | nobody | DB on-call | breaks the runbook |
| Customers | as now | small lag risk at peak | risk of stale invoice totals, as in staging |
| Finance | BI-140 can start 11-06 | BI-140 can start 11-04 | BI-140 can start 11-03 |

Finance's dashboard keeps working on `total_text` in every option. The choice only changes when BI-140 can start.

**Options**

**A: Split W4 by month across about 4 nights**
- Pros: Same conditions as W1–W3, which all verified cleanly. Needs no one's sign-off. Each night verifies a smaller slice.
- Cons: Slowest, so BI-140 waits about 2 days longer than with B. It takes 4 nights of someone running and verifying. Month boundaries need per-month row counts, which I don't have.

**B: Night runs plus throttled daytime runs**
- Pros: Finishes about 2 days sooner than A while staying within the runbook.
- Cons: Daytime load during peak hours. Its safety rests on the "~100k rows/hour, throttled" figure in the runbook, which I haven't seen measured on production. Needs the on-call's agreement and attention.

**C: One run, as queued**
- Pros: Fastest, and nothing to plan.
- Cons: About 16 hours at full speed during the day, which the runbook forbids. It risks the replica lag that showed customers stale invoices.

**Recommendation: A, firm.** It rests on the measured rate of about 149k rows an hour. B is the strongest alternative, but nothing on record makes BI-140 urgent: there's no deadline in `TICKETS.md`. Two days don't justify daytime load on the database behind customer invoices. If finance has a deadline, B becomes the better choice.

## Question 2: Has W4 already started?

**Context.** `waves.log` still says "queued: next night window". The nights of 10-31 and 11-01 have passed with no entry. Either W4 hasn't run, or it ran (possibly partly) and the log wasn't updated. The project files can't settle this; only the database or the person running it can. The answer decides whether the team status says "not started" or "partly done". If W4 is partly done, A and B pick up the remaining rows: the script skips rows that already have `total_minor`, so it can safely restart. Any partial run also needs verifying before more W4 runs.

**Your answers**
1. How should W4 run: **A** (4 nights), **B** (nights plus throttled days), or **C** (one run)?
2. Did W4 run on 10-31 or 11-01: **no**, **partly**, or **don't know**?
3. Does finance have a deadline for the BI-140 dashboard switch: **yes** (when?) or **no**?
