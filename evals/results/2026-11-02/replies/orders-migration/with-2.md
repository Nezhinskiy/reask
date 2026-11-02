Here are the three questions again, with what you need to answer them.

**Context (applies to all three)**

The goal is a new `region` column on `orders` that can never be empty. It's filled from the customer's billing country, and the tax report (TAX-19) needs it by Dec 1, four weeks from today. Until then that report can show orders without a region as "unknown". Nothing has been written yet; the migration waits on these answers.

The repo has three files:
- `db/schema.sql`: `orders` has about 40 million rows and takes about 25,000 new orders an hour at peak. `customers.billing_country` is a 2-letter code like `DE` and is always filled.
- `app/orders.py`: a comment says region will be the billing country "mapped through `REGIONS`", meaning a country → region lookup. That lookup doesn't exist anywhere in the repo.
- `OPS.md`: migrations run inside the deploy job, which is killed after 10 minutes. An alarm fires when the database copy (replica) falls 30 s behind. Last month, rewriting every row of the `payments` table blocked new writes for 6 minutes and caused an outage (INC-212).

So filling 40M rows in one statement inside a deploy isn't an option: it would likely be killed at 10 minutes and could repeat INC-212.

---

### Question 1: What does a country become?

`REGIONS` is the lookup that turns a country code into a region, and it isn't in the repo. I need its values, and what happens when a country isn't in it.

**Options for an unmapped country**
- **A. Store `'UNKNOWN'`**
  - Pros: an order is never rejected over reporting data.
  - Cons: gaps in the lookup hide quietly in tax data until someone queries for them.
- **B. Reject the order**
  - Pros: a gap in the lookup shows up immediately.
  - Cons: a missing tax entry blocks real sales.

**Recommendation:** A, leaning. A tax field shouldn't stop checkout. The strongest case for B is that tax data must be complete, but a nightly count of `'UNKNOWN'` rows catches gaps without losing sales.

**Question:** Where is `REGIONS` defined (or what are the regions, e.g. `EU`/`NA`/`APAC`), and should unmapped countries get `'UNKNOWN'` or be rejected?

---

### Question 2: Which country for old orders?

The 40M existing orders have to be filled from somewhere. The only source is the customer's *current* billing country. The schema has no history of past addresses.

**Example:** a customer ordered in 2024 with a German address and moved to the US in 2025.

| | Region on the 2024 order |
|---|---|
| Use current country | `NA`: wrong for tax purposes |
| Use country at order time | `EU`: correct, but needs a source the repo doesn't have |

**Options**
- **A. Use the current billing country**
  - Pros: possible today, with no extra data.
  - Cons: anyone who moved gets misreported on their older orders, in a tax report.
- **B. Use the country at the time of the order**
  - Pros: correct.
  - Cons: needs an address history or old invoices from somewhere outside this repo, and may not be ready by Dec 1.

**Recommendation:** close call; it depends on a fact I can't see. If TAX-19 only covers recent periods, or tax doesn't care about customers who moved, A is fine. If it reports on past years, A produces wrong numbers.

**Question:** Is filling old orders from the customer's current billing country acceptable for the tax report, or does it need the country at the time of the order? If the latter, where does that data live?

---

### Question 3: How to roll it out safely

Every option fills old rows with a separate script that runs outside the deploy job. It updates a few thousand rows at a time and pauses whenever the replica falls behind. The options differ in how the column becomes "never empty".

- **A. Original plan: empty first, enforce at the end.** Add the column empty (instant), make new orders write it, run the script, then add the NOT NULL rule in a way that doesn't block writes.
  - Pros: no placeholder values; NULL clearly means "not filled yet".
  - Cons: three migrations, and the final check reads all 40M rows. The column isn't actually protected until the last step.
- **B. New: enforced from day one with a placeholder.** Add the column as NOT NULL with default `'UNKNOWN'`. On Postgres 15 that's instant, with no table rewrite. Make new orders write the real region, have the script replace `'UNKNOWN'` on old rows, then remove the default so a missed write fails loudly.
  - Pros: the column is never empty from the first deploy, with fewer steps and no full-table check.
  - Cons: until the script finishes, `'UNKNOWN'` looks like real data. Anyone querying must know it means "not filled yet", and it overlaps with Question 1's `'UNKNOWN'` for unmapped countries.
- **C. A single migration, in a maintenance window**
  - Pros: simplest.
  - Cons: 40M row updates in one go is what caused INC-212, and it would exceed the 10-minute deploy limit.

**Recommendation:** B, leaning. It wasn't in my original question; I'm suggesting it now because Postgres 15 can add a NOT NULL column with a fixed default instantly. The case for A is that a placeholder can be mistaken for a real value. It doesn't win here because OPS.md already lets reports show "unknown" until Dec 1, and the script's progress is easy to track by counting `'UNKNOWN'` rows.

**Question:** Which rollout: B (placeholder `'UNKNOWN'`, enforced from day one), A (empty first, enforce at the end), or C (one migration in a maintenance window)? Either A or B also needs your OK to run the fill script outside the deploy job.
