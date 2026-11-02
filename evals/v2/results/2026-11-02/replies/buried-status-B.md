# buried-status, cell B

## Run 1

all-decisions FAIL, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 450 words

You need to make two decisions about the last backfill run (W4) before the team update can go out.

## 1. How should W4 run?

**Context.** MIG-21 adds a `total_minor` column to `orders` that stores each order's total as whole cents. A backfill script fills it in for old orders, one group of order years (a "wave") at a time. Waves W1–W3 (2019–2023) are done and verified. W4 covers 2024–2026, which is 3,288,907 rows. It's queued as one overnight run. The finance revenue dashboard (BI-140) can't move to the new column until W4 is finished.

**Decided:** the runbook rules. Runs are unthrottled only between 22:00 and 04:00. Daytime runs must be slowed down and need the database on-call's OK. Batches stay at 5,000 rows or fewer, because bigger ones made customer invoices show stale totals.

**The problem.** W1–W3 each ran at about 150,000 rows an hour. At that rate W4 takes about 22 hours. A single run starting at 22:00 would still be going at full speed the next afternoon, during peak traffic. W3 (903,552 rows) already ran 4 minutes past 04:00.

| | W4 runs as | Finishes | Needs |
|---|---|---|---|
| Single run (current plan) | 1 run, ~22 h, mostly daytime | 1 day | breaks the runbook |
| (a) Split by month, nights only | ~750–800k rows per night | ~5 nights | nobody's sign-off |
| (b) Slowed daytime runs | ~100k rows/h | ~33 daytime hours, or ~2–3 days if combined with nights | on-call agreement |

**(a) Split by month, nights only**
- Pros: follows the runbook exactly. Each night is the same size as a wave that already went fine.
- Cons: the dashboard switch waits about 5 more days.

**(b) Slowed daytime runs, alone or added to nights**
- Pros: finishes days sooner.
- Cons: adds database load during business hours and needs on-call approval.

**Recommendation: (a), firm.** The tickets set no deadline for the dashboard, so the extra few days cost nothing concrete. If there is a deadline, that would tip it to (b).

**Should W4 be split into about 5 night runs (a), or sped up with slowed daytime runs that the on-call approves (b)?**

## 2. Has W4 already started?

**Context.** The log says W4 runs "next night window", but there's no entry for the nights of Oct 31 or Nov 1. I can't see the database from here. The script skips rows it already filled, so a partial run is safe to continue. Your answer changes only whether the update says "not started" or "partly done".

**Did W4 run on Oct 31 or Nov 1, at least in part?** (yes / no / don't know)

---

## Run 2

all-decisions PASS, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 517 words

We still need to decide how to run the last batch of the backfill. The backfill is the job that fills the new cents column for old orders. I also have a smaller question about whether that batch has already started.

**Context (applies to both questions)**

MIG-21 moves order totals from a free-text column (`total_text`, e.g. "1234.50") to an integer column in cents (`total_minor`). Old orders are filled in four batches ("waves"), grouped by order year. Waves 1–3 (2019–2023) are done and checked with no errors. Wave 4 still has to run: orders from 2024–2026, 3,288,907 rows. Two things wait on it: switching the finance "Revenue by day" dashboard to the new column (ticket BI-140), and later deleting the old column.

The runbook (the team's rules for this job) says:
- Runs go in the night window, 22:00–04:00.
- Daytime runs must be slowed down (`--throttle-ms 50`, about 100,000 rows an hour) and need the database on-call engineer's agreement.

The plan in the log is to run wave 4 in one go next night.

---

**Question 1: how should wave 4 run?**

Waves 1–3 each processed about 150,000 rows an hour. At that rate wave 4 takes about 22 hours. Run in one go from 22:00, it would still be going at full speed until about 20:00 the next evening, through peak order traffic. The runbook doesn't allow that. Wave 3 already ran 4 minutes past 04:00.

| | Single run (current plan) | A: split across nights | B: add slowed daytime runs |
|---|---|---|---|
| Runs | about 22 h straight | about 4–5 nights of about 800k rows | nights plus throttled days |
| Finished (from tonight) | about 11-03 evening | about 11-06/07 | about 11-04/05 |
| Within the runbook? | No | Yes | Yes, if on-call agrees |

**A: split wave 4 by month** (`--months`, e.g. `2024-01..2024-06`), one chunk per night.
- Pros: same conditions as waves 1–3, which went cleanly; nobody's sign-off needed.
- Cons: the dashboard switch waits about 2–3 days longer; the rows per month aren't known yet, so the first night's chunk is a guess.

**B: slowed daytime runs, alongside night runs.**
- Pros: finishes about 2 days sooner.
- Cons: needs the on-call engineer's agreement; it runs during customer traffic, which is the risk the runbook exists to limit.

**Recommendation:** A, firmly. Nothing is waiting on a deadline, and A is the only option that stays within the rules without anyone else signing off.

---

**Question 2: has wave 4 already started?**

The log says "queued: next night window", but there are no entries for the nights of 10-31 or 11-01. Either it didn't run, or it ran and nobody updated the log. I can't check the database from here. Restarting is safe either way, because the job skips rows that are already filled. The answer only changes whether the team post says "not started" or "partly done".

---

1. For wave 4: **A** (split across nights) or **B** (add slowed daytime runs)?
2. Has wave 4 started: **no**, **yes, partly**, or **not sure**?

---

## Run 3

all-decisions PASS, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 586 words

Two things are holding up the MIG-21 team status update, and both need an answer from you.

**Context (applies to both):** MIG-21 is moving order totals from a free-text column (`total_text`, e.g. "1234.50") to a whole-number cents column (`total_minor`). Old orders are being filled in by a script, in four batches by order year called "waves". W1–W3 (2019–2023) are done and checked. W4 covers 2024–2026, with 3,288,907 orders, and hasn't run. The finance revenue dashboard (BI-140) can't switch to the new column until W4 is finished and checked.

---

### Question 1: How should W4 be run?

**Context.** The runbook (the team's rules for this script) says:
- Run at night, 22:00–04:00, when order traffic is low. That's 6 hours.
- Daytime runs are allowed only if slowed down (about 100,000 orders an hour) and the database on-call person agrees.

W1–W3 each filled about 150,000 orders an hour. At that rate W4 needs about 22 hours. Run in one go as currently planned, it would carry on at full speed into the next day's busy hours, which the rules don't allow. W3 alone already went 4 minutes past 04:00.

**Example: how long W4 takes under each option**

| | Per session | Sessions | Finished |
|---|---|---|---|
| A: nights only | ~660k orders (~4.5 h) | 5 nights | ~5 days |
| B: nights + slowed daytime runs | ~660k night + ~800k day (8 h) | ~2–3 days | ~2–3 days |
| As planned (one run) | 3.29M | 1 | ~22 h, mostly outside the night window |

I've assumed the 2024–2026 orders are spread roughly evenly across months, about 97k a month. If recent months are busier, each night should cover fewer months. A quick count per month before each night would settle that.

**Options**

**A: Split W4 by month over about 5 nights.**
- Pros: follows the rules as written, needs nobody's sign-off, and is the same setup that worked for W1–W3.
- Cons: the dashboard switch and the 30-day countdown to deleting the old column both start about 2–3 days later.

**B: Nights plus slowed daytime runs.**
- Pros: finishes about 2–3 days sooner.
- Cons: runs during customer traffic. In testing, heavy writes delayed the read-only database copy, and the invoice page showed customers out-of-date totals. It also needs the on-call person's time and agreement.

**Recommendation: A, leaning.** The strongest case for B is speed. But the gain is a few days on a migration whose last step waits 30 days anyway. That's not worth risking wrong invoice totals in front of customers.

---

### Question 2: Has W4 already started?

**Context.** The run log says W4 is planned for "the next night window". Two nights (Oct 31 and Nov 1) have passed with nothing written in the log. Either it never ran, or it ran (fully or partly) and nobody logged it. A partial run is harmless: the script skips orders it has already filled, so it can safely be started again. The answer only changes how the update describes W4.

**Options**
- **Not started:** the update says "W4 not started".
- **Partly or fully run:** the update says how far it got, and the log needs catching up.
- **Don't know:** the update says "W4 status being checked", and someone checks the database.

---

**1. Should W4 run as A (nights only, about 5 nights) or B (nights plus slowed daytime runs)?
2. Has W4 started: not started, partly or fully run, or don't know?**
