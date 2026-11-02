Here are the questions again, with the background you need.

## What we're doing

The goal is a new required (`NOT NULL`) `region` column on `orders`. Ticket TAX-19 needs it for the tax report, due Dec 1, which is four weeks away. Until then, reports may show a missing region as "unknown". Nothing has been written yet. The migration waits on your answers.

The repo has three files:
- **`db/schema.sql`**: `orders` has about 40 million rows and takes about 25,000 new orders an hour at peak. `customers` has one `billing_country` per customer (a two-letter code such as `DE`). Nothing records past billing countries or the country at the time of each order.
- **`app/orders.py`**: a comment in `create_order` says region will come from `billing_country` "mapped through `REGIONS`". `REGIONS` isn't defined anywhere in the repo.
- **`OPS.md`**: the database is Postgres 15 with one primary and one read-only replica that copies it. Migrations run inside the deploy job, which is killed after 10 minutes (DEPLOY-3). An alarm fires if the replica falls 30 seconds behind. Last month a 6-minute rewrite of the `payments` table blocked writes and caused an outage (INC-212).

**Decided:** nothing yet. My earlier message listed three questions. I've split the first into two, so there are four below.

---

## 1. Where the country → region mapping comes from

**Context:** every order gets its region from a lookup: billing country in, region out. The lookup doesn't exist yet. I don't know the region values either: they could be broad areas (`EU`, `NA`, `APAC`) or tax jurisdictions.

**Options**
- **A. You point me to an existing mapping** (another repo, a service, a spreadsheet the tax team owns).
  - Pros: tax already trusts it.
  - Cons: if it lives outside this codebase, someone has to keep the copy in sync.
- **B. A small database table, `country_regions(country, region)` (new option).**
  - Pros: the app and the backfill of old orders (question 3) read the same data, and the backfill becomes a plain SQL join.
  - Cons: one more table, and someone still has to supply the values.
- **C. A Python dict in the app code.**
  - Pros: simplest, and changes go through code review.
  - Cons: SQL can't read it, so the backfill has to run through Python and gets slower.

**Recommendation:** leaning B, filled from A if a mapping already exists. B loses if the mapping is short and stable and you'd rather keep it in code. Then C is fine.

**Question:** does a country → region mapping already exist? If so, where? If not, what region values does the tax report expect, and should the mapping live in a database table or in code?

---

## 2. What happens when a country isn't in the mapping

**Context:** a customer's country may be missing from the mapping, for example a newly added code. The column can't be left empty, so the app has to do something.

**Options**
- **A. Store `'UNKNOWN'` and log a warning.**
  - Pros: the order always goes through.
  - Cons: the tax report quietly misses those orders unless someone watches the log.
- **B. Reject the order.**
  - Pros: no bad data can get in.
  - Cons: a customer loses a purchase over a reporting field.
- **C. Cover every ISO country code, enforced by a test, with A as a last resort (new option).**
  - Pros: in practice the gap can't happen.
  - Cons: someone has to assign a region to roughly 250 countries.

**Recommendation:** leaning C. The argument for B is that `'UNKNOWN'` is wrong data in a tax report. It doesn't win because a failed checkout costs more than one row that needs fixing, and an alert finds those rows.

**Question:** when a billing country has no region, should the order store `'UNKNOWN'`, fail, or should we make the mapping complete so the case can't arise?

---

## 3. Which country to use for the 40 million existing orders

**Context:** old orders need a region too. The only country on record is each customer's *current* billing country. Example: a customer billed in `DE` in March who moved to `FR` in June would have the March order tagged with France's region. Nothing in this repo records the country at the time of the order. It might exist elsewhere, in invoices or the payment provider.

**Options**
- **A. Use the current billing country.**
  - Pros: possible today, with no extra source.
  - Cons: orders from customers who moved land in the wrong region on a tax report.
- **B. Use a historical source outside this repo.**
  - Pros: correct.
  - Cons: depends on that source existing and on joining it in. That work has to fit in four weeks.
- **C. Mark old orders `'UNKNOWN'`.**
  - Pros: honest.
  - Cons: the tax report gets nothing useful for past periods.

**Recommendation:** leaning A. B wins if tax needs exact past jurisdictions. I can't check from here how often customers change billing country, and that's the fact that would change my mind.

**Question:** for orders placed before this change, is the customer's current billing country good enough for TAX-19? Or does it need the country as it was when the order was placed, and if so, where is that recorded?

---

## 4. How to roll it out

**Context:** the obvious single migration would add the column, fill all 40M rows and require a value. Filling 40M rows takes longer than the deploy job's 10-minute limit. It also makes the database write a copy of every row, which pushes the replica far past its 30-second alarm. That's the same kind of change that caused INC-212.

**Options**
- **A. Five steps (my proposal):**
  1. Add the column as optional. This takes about a second.
  2. The app starts filling it on new orders.
  3. A separate script fills old orders in small batches outside the deploy job, pausing whenever the replica falls behind.
  4. A check that no row is empty is added and then verified, without blocking writes.
  5. The column is made required.
  - Pros: no blocked writes and no timeouts.
  - Cons: three deploys plus a script that someone has to run and watch, spread over a few days.
- **B. One migration in a maintenance window.**
  - Pros: one step, easy to understand.
  - Cons: orders stop during the window, and the replica still falls far behind.

**Recommendation:** firm on A. The table's size, the 10-minute limit and INC-212 all rule out B.

**Question:** can we roll this out in the five steps above, with a backfill script that someone runs outside the deploy job?
