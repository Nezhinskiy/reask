# buried-status, cell C

## Run 1

all-decisions FAIL, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 1198 words

I couldn't re-check the files just now. The Read and Grep tools were denied in this mode, so I didn't try to work around that. Everything below comes from reading the files earlier in this session. I redid the arithmetic just now; it isn't freshly checked against the files.

## What we're doing and why it needs a decision now

**MIG-21** is the ticket to stop storing order totals as free text. The `orders.total_text` column holds values like `"1234.50"` or `"N/A"`. We're adding `orders.total_minor`, the same amount as a whole number of cents (`123450`).

The plan has five steps:
1. Write both columns for new orders. This is done.
2. Fill in the old orders ("backfill") in four **waves** by order year: W1 to W4.
3. Verify each wave.
4. Move the finance dashboard over to the new column.
5. Drop the old column.

W1–W3 are done and verified. **W4 is next and is queued as one overnight run.** At the speed of the earlier waves, it won't fit in one night. So the decision is how to run W4, and it has to be made before the next night window, which starts at 22:00 tonight.

## What the codes, names and numbers mean

| Term | Meaning |
|---|---|
| MIG-21 | The ticket for this migration |
| `total_text` / `total_minor` | Old free-text total / new integer total in cents |
| #88, release 4.12 | The change that writes both columns for every new or edited order. Merged 2026-10-27. |
| W1, W2, W3, W4 | Backfill waves: 2019–20 (412,380 rows), 2021–22 (826,114), 2023 (903,552), 2024–26 (3,288,907) |
| `backfill_totals.py` | The backfill script. It fills `total_minor` in batches of 5,000 rows and skips rows that already have a value, so it's safe to restart. |
| Night window | 22:00–04:00 (6 hours). This is the runbook's default slot because order traffic is lowest then. |
| `--throttle-ms 50` | A pause between batches. It's required for daytime runs (about 100,000 rows/hour) and needs the DB on-call's agreement. |
| Read replica | A copy of the database that the invoice API reads from. Heavy writes can make it fall behind. |
| `verify_totals` | The per-wave check. Unparseable `'N/A'` rows may stay empty; any other failure blocks the next wave. |
| 37 in W3 | Old cancelled test orders with `'N/A'` totals, left empty as the runbook allows |
| BI-140 | The ticket to switch the finance "Revenue by day" dashboard to `total_minor`. It's blocked until W4 is done. |
| 30 days | How long after the dashboard switch `total_text` may be dropped |

## The fact the recommendation rests on

Here is how fast the earlier waves ran:
- W1: 412,380 rows in 2h47m, about 148k rows/hour
- W2: 826,114 rows in 5h31m, about 150k/hour
- W3: 903,552 rows in 6h04m, about 149k/hour. It ran 4 minutes past 04:00.

At that speed:
- W4's 3,288,907 rows take about **22 hours**.
- One night can do at most about 894k rows, so W4 needs **at least 4 nights**. With a safety margin it's more like 5, at about 750–800k rows a night.
- The script has no stop time. If nobody stops it, it keeps running.

## Live example

A 2024 order with `total_text = "1234.50"` gets `total_minor = 123450`. The value comes out the same under every option; only the timing differs.

If W4 is started as queued at 22:00 tonight:
- By 04:00 on 3 Nov, about 0.9M rows are done and about 2.4M remain.
- From 04:00 it keeps running unthrottled through the day and finishes around **20:00 on 3 Nov**.

If it's split by month instead, it finishes after about 5 nights, around the morning of 7 Nov. Verification would come after that.

## What users would see

- **Customers:** suppose a customer gets a refund at 11:00 on 3 Nov and opens their invoice. If the database copy the invoice API reads from has fallen behind during a daytime run, the invoice still shows the old total. This happened in the staging test, where the copy fell up to 4 minutes behind with 20,000-row batches. Nobody has tested 5,000-row batches during daytime traffic, so this is a risk, not something we've seen.
- **Finance:** their dashboard doesn't change until BI-140. The only difference between the options is how many days they wait.

## Options

**(a) Split W4 by month across about 5 night windows (recommended)**
- Pros:
  - Stays within the runbook and needs nobody's sign-off.
  - Puts no load on the database during the day.
  - Each chunk can be verified on its own, so a problem stops after one night, not after 3.3M rows.
- Cons:
  - Finance waits about 5 more nights, plus verification.
  - Five runs to schedule.
  - The per-month row counts aren't in the repo, so the first chunk has to be sized by estimate.

**(a′) Same as (a), but start the full W4 each night and stop it at 04:00**
- Pros: no need to size chunks. This works because the script is safe to restart.
- Cons:
  - Someone has to stop it by hand every night.
  - Verification happens only once at the end.
  - Stopping mid-batch loses up to 5,000 rows of work, which is harmless.

**(b) Throttled daytime runs (about 100k rows/hour) on top of the nights**
- Pros: finishes in about 2–3 days instead of 5.
- Cons:
  - Needs the DB on-call to agree.
  - Puts load on the database during customer traffic, with some risk of stale invoices.
  - Someone has to watch the daytime runs.

**(c) Run it as queued, in one go**
- Pros: one command and no replanning. It's the fastest, finishing about 20:00 tomorrow.
- Cons:
  - About 16 hours of it run unthrottled outside the window, which the runbook doesn't allow.
  - This carries the highest risk of stale customer invoices.
  - There's no checkpoint before 3.3M rows are done.

## How sure I am

- **That one run won't fit in one night:** high. The 22-hour estimate is 3.7 times the 6-hour window, so small errors in the speed don't change the answer. The caveat is that I couldn't reopen the log just now.
- **On "about 5 nights":** medium. Newer rows might go faster or slower, and the 3.29M may include a few thousand rows already filled by refunds or new orders.
- **Whether W4 has already started:** unknown. The log has no entry for the nights of 31 Oct or 1 Nov.

## Questions for you

1. Which option should we take: (a), (a′), (b) or (c)?
2. Did W4 start on 31 Oct or 1 Nov, even partly? This changes the remaining row count and what the status says.
3. Is there a deadline for finance on BI-140 that would justify (b)'s faster finish? If so, who is the DB on-call to ask?
4. Who runs the nightly job? For (a′), can they stop it at 04:00?
5. Do you want to allow file reads in this session so I can re-check the log, runbook and script before the status goes out?

---

## Run 2

all-decisions FAIL, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 967 words

I couldn't recheck the files just now. This turn, reading the project was denied ("don't ask" mode), so I didn't try other ways in and I changed nothing. Every fact below comes from my full read of the files earlier in this session. The arithmetic is redone here. Rerun the check yourself, or let me read again, if you want it confirmed from the files.

## What we're doing

**MIG-21** is the ticket to store order totals as whole numbers of cents instead of free text. Today `orders.total_text` holds strings carried over from the old shop, like `"1234.50"` or `"N/A"`. We are adding `orders.total_minor`, a whole-number column in cents ("minor units"), filling it for every order, and moving readers to it. `total_text` gets dropped 30 days after the last reader has moved.

The **backfill** fills `total_minor` for existing orders, one group of order years (a **wave**) at a time. `backfill_totals.py` reads each order's `total_text` and turns `"1234.50"` into `123450`. It writes 5,000 rows per **batch**, and only touches rows where `total_minor` is still empty, so a stopped run can be restarted safely.

## Every code, number and name

| Term | Meaning |
|---|---|
| **#88** | The pull request that makes new and edited orders write both columns ("dual-write"). Merged 2026-10-27. |
| **4.12** | The release that shipped #88. |
| **BI-140** | Ticket to switch finance's "Revenue by day" dashboard from `total_text` to `total_minor`. It can't start until every order is filled. |
| **W1–W4** | Waves. W1 = orders from 2019–2020 (412,380 rows), W2 = 2021–2022 (826,114), W3 = 2023 (903,552), W4 = 2024–2026 (3,288,907). |
| **Night window** | 22:00–04:00, when order traffic is lowest. It's the runbook's default time to run. |
| **`--throttle-ms 50`** | Pause 50 ms between batches. The runbook requires it for daytime runs, together with the **DB on-call's** agreement (the engineer on duty for the database). It gives about 100,000 rows/hour. |
| **`--months`** | Script option to run only some months, e.g. `2024-01..2024-06`. This is how a wave is split. |
| **Batch ≤ 5,000** | Runbook limit. In staging, 20,000-row batches put the **read replica** (a read-only copy of the database) up to 4 minutes behind. The **invoice API** reads from that replica, so customers saw out-of-date invoice totals. |
| **`verify_totals`** | The check run after each wave. Any mismatch, or any unparseable value other than `'N/A'`, blocks the next wave. |
| **37 / `'N/A'` / `cancelled_test`** | W3 had 37 rows with text `'N/A'`. All were cancelled test orders from the old shop. The runbook says to leave them empty and record the count. |

**Status:** dual-write is live. W1, W2 and W3 are done and verified with 0 mismatches. W4 is queued as one night run. BI-140 and dropping `total_text` wait on W4.

## Why a decision is needed now

W4 is queued for the next night window as one run, and it doesn't fit in one night.

- W1 took 2h47m, about 148k rows/hour. W2 took 5h31m, about 150k/h. W3 took 6h04m, about 149k/h, and finished at 04:04, 4 minutes past the window.
- 3,288,907 rows ÷ about 149k/h ≈ **22 hours**. Started at 22:00, the run would go on, unthrottled, until about **20:00 the next day**, right through peak traffic. The runbook doesn't allow that.

**Live example:** at 22:00 the run starts on 2024 orders. At 04:00 it's only about 27% done. From 04:00 to 20:00 it keeps writing 5,000-row batches at full speed while customers are placing orders.

**What customers would see:** at 14:00 a customer opens the invoice for an order that was just refunded. Under the extra load the replica lags, the same failure seen in staging, and the invoice shows the old total. Under options (a) and (b) below, this doesn't happen. What changes instead is how long finance waits for BI-140.

## Options

**(a) Split W4 by month over about 5 night windows, about 650–800k rows a night (recommended)**
- Pros: stays inside the runbook and needs nobody's sign-off. Each night matches a load already proven three times. It's restartable, and it can be verified one part at a time.
- Cons: slowest option. Starting tonight, it ends around 11-06/07, so BI-140 slips by that much. It means 5 runs to watch and 5 checks. The month boundaries have to be chosen from a row count per month, which I don't have.

**(b) Throttled daytime runs plus night runs**
- Pros: could finish in about 2–3 days.
- Cons: needs the DB on-call to agree. It adds load at peak time, even throttled. At about 100k/h that's still roughly 33 hours of daytime running if used alone. The daytime replica effect hasn't been tested.

**(c) Run as queued, one 22-hour run**
- Pros: one run, done in about a day.
- Cons: breaks the runbook. It runs unthrottled through the day, and it carries the risk of customers seeing stale invoices.

## How sure I am

- **High** that W4 can't fit in one night: three waves gave the same rate within about 1%.
- **Medium** on the exact night count. 2024–2026 rows could process at a different speed, more likely slower than faster.
- Not rechecked against the files this turn, for the reason given at the top.

## Open questions

1. Which option do you want: **(a)**, **(b)**, or **(c)**?
2. Did W4 start on the night of 10-31 or 11-01? The log has no entry for either night, so I can't tell whether it's not started or partly done.
3. If (a): can someone run a row count per month for 2024–2026 so the nights can be sized? If (b): who is the DB on-call to ask?
4. Does BI-140 have a deadline that makes about 5 nights too slow?

---

## Run 3

all-decisions FAIL, decision-1 PASS, facts PASS, no-trap-pick PASS, references FAIL; 1167 words

# MIG-21 recap: one decision needed on backfill wave W4

## What we're doing and why this decision is needed now

The shop's order totals are stored as free text. We're moving them into a proper integer column. Three of the four backfill batches ("waves") are done and verified. The last and largest one, W4, is queued as one overnight run, but the numbers say it can't finish in one night. If it starts tonight as queued, it will still be running unthrottled at peak daytime traffic tomorrow, which the team's runbook forbids. So the choice has to be made before tonight's 22:00 run.

## What each code, number and name means

| Term | Meaning |
|---|---|
| **MIG-21** | The ticket for this migration: store order totals as integer cents instead of text. |
| **`total_text`** | The old column. Totals are text carried over from the old shop, e.g. `"1234.50"` or `"N/A"`. |
| **`total_minor`** | The new column: the total in cents (BIGINT). "Minor units" means cents. |
| **#88 / release 4.12** | The PR that makes new and edited orders write both columns ("dual-write"). Merged 2026-10-27 and shipped in 4.12. |
| **Backfill** | `backfill/backfill_totals.py` fills `total_minor` for older orders. It never overwrites a value that's already set, so it's safe to restart. |
| **W1–W4** | The waves, split by order year: W1 = 2019–20, W2 = 2021–22, W3 = 2023, W4 = 2024–26. |
| **Night window 22:00–04:00** | The default slot for runs, when order traffic is lowest. |
| **Batch 5,000** | Rows written per commit. The runbook caps it at 5,000 because in staging, 20,000-row batches left the **read replica** (a read-only copy of the database) up to 4 minutes behind. |
| **Invoice API** | Reads from that replica, so when the replica lags, customers see old invoice totals. |
| **`--throttle-ms 50`** | A pause after each batch. Required for daytime runs, together with the **DB on-call**'s (database duty engineer's) agreement. The runbook says throttled runs do about 100k rows/hour. |
| **`--months`** | A script option that runs only part of a wave, e.g. `2024-01..2024-06`. |
| **`verify_totals`** | The check run after each wave. Any mismatch, or any unparseable value other than `'N/A'`, blocks the next wave. |
| **37 / `cancelled_test`** | The 37 W3 rows left empty because their text is `'N/A'`. They're cancelled test orders, which the runbook allows. |
| **BI-140** | The ticket to switch finance's "Revenue by day" dashboard to the new column. It's blocked until W4 is finished. |
| **30 days** | `total_text` gets dropped 30 days after the last reader stops using it. |

## Live example

For one order, the backfill does this:

| `total_text` | `total_minor` after the backfill |
|---|---|
| `"1234.50"` | `123450` |
| `"N/A"` | stays empty (NULL) |

**The fact the decision rests on is speed.** All three finished waves ran at the same pace:

| Wave | Rows | Time | Rows/hour |
|---|---|---|---|
| W1 | 412,380 | 2h47m | ~148k |
| W2 | 826,114 | 5h31m | ~150k |
| W3 | 903,552 | 6h04m (ended 04:04, 4 min over) | ~149k |
| **W4** | **3,288,907** | **~22h at that pace** | — |

A 6-hour night window fits at most about 890k rows, and W3 already overran it by 4 minutes. If W4 starts tonight at 22:00 as one run, it ends around **20:00 tomorrow (11-03)**, running unthrottled through the whole business day.

**UX example (what customers might see).** A customer gets a refund at 14:00 tomorrow and opens their invoice. If the backfill's writes are making the replica lag, the invoice can still show the pre-refund amount for minutes. Staging saw up to 4 minutes of lag, though that was with 20k-row batches. Nobody has measured 5k-row batches at daytime traffic. Finance users are affected only indirectly: the later W4 finishes, the later their dashboard switches over.

## Options

**(a) Split W4 by month over about 5 nights** (~650–800k rows per night with `--months`)
- Pros: fully within the runbook. No customer-facing risk, since it only runs at low traffic. No sign-off needed. Each piece can be restarted safely.
- Cons: slowest option. Starting tonight, it finishes around 04:00 on **11-07**, which delays BI-140 by about 4 days. Someone has to start 5 runs. Month boundaries have to be chosen so each night fits, and order volume per month isn't in the repo.

**(b) Throttled daytime runs, combined with the night runs**
- Pros: fastest compliant option. Roughly 1.7M rows per 24 hours, so done in about 2 days (around 11-04).
- Cons: needs the DB on-call to agree. It writes during peak traffic, so there's some replica-lag and stale-invoice risk. Also, I suspect the 50 ms throttle protects very little at this batch size. At ~30 batches/hour it adds only about 1.5 s/hour of pause, so the runbook's 100k/hour is probably daytime load, not the throttle doing much. That means daytime runs would be nearly unthrottled in practice. This is my inference, not something measured.

**(c) Run it as queued: one run of about 22 hours**
- Pros: the simplest, and done by about 20:00 tomorrow.
- Cons: breaks the runbook (unthrottled during the day, no on-call sign-off). It carries the highest risk of customers seeing stale invoices, and if it has to be stopped, someone has to restart it by hand.

**I recommend (a).** Option (b) is fine if the 4 days matter to finance and the DB on-call agrees.

## How sure I am, and what I couldn't re-check

- **The arithmetic: high confidence.** Three waves agree within 1%, so ~22 hours for W4 is solid. Even if a tenth of W4's rows were already filled by dual-write or refunds, it would still take about 20 hours.
- **The re-check you asked for: I couldn't do it.** When I tried to re-read `waves.log` and `RUNBOOK.md` just now, file access was denied (the session is in "don't ask" mode). All the numbers above come from my reads of those files earlier in this session. I didn't change any files.
- **Unknown:** whether W4 already ran partly on 10-31 or 11-01. The log has no entry for those nights, and I can't see the database.

## Open questions

1. **Which option: (a) 5 nights, (b) daytime plus nights with the on-call's agreement, or (c) the single run as queued?**
2. Did W4 already start on 10-31 or 11-01, or do you know who would know? If part of it ran, it needs fewer nights.
3. If (b): who is the DB on-call, and are they okay with daytime runs? Would you also like the throttle's real effect measured before relying on it?
4. Does finance (BI-140) have a deadline that would make the 4-day difference between (a) and (b) matter?
5. Do you want to allow file reads again so I can re-verify the numbers before you post?
