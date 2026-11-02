No problem. Here is the full picture again. I haven't written anything yet.

**Context (applies to all three questions)**

You asked for a new required (NOT NULL) `region` column on `orders`, filled from each customer's billing country. The tax report needs it (ticket TAX-19, due Dec 1, four weeks from today). Until then, reports may show a missing region as "unknown". The repo has three relevant files:

- `db/schema.sql`: `orders` has about 40M rows and takes about 25k new orders an hour at peak. `customers.billing_country` is a required 2-letter country code. There's no history of past billing countries.
- `app/orders.py:2`: a comment says region will be "`billing_country` mapped through `REGIONS`". `REGIONS` doesn't exist anywhere in the repo.
- `OPS.md`: Postgres 15, one primary database and one read copy (replica). Migrations run inside the deploy job, which is killed after 10 minutes (DEPLOY-3). An alarm fires if the replica falls more than 30 s behind. Last month a 6-minute rewrite of the `payments` table blocked writes and caused an outage (INC-212).

**Decided:** nothing yet. **My assumption:** filling all 40M existing orders in one statement is off the table. It would likely run past the 10-minute limit and repeat INC-212.

---

### Question 1: How does a country become a region?

**Context.** The code promises a `REGIONS` mapping, but it doesn't exist, and I don't know what a "region" is for TAX-19. It could be a broad zone (`EU`, `NA`, `APAC`) or a tax jurisdiction. Because the column is required, every country also needs *some* value, including countries the mapping doesn't cover.

**Options for unmapped countries:**
- **A. Store `'UNKNOWN'`**
  - Pros: orders never fail, and it matches OPS.md's "treat missing as unknown".
  - Cons: misclassified orders pile up quietly unless someone watches the count.
- **B. Reject the order**
  - Pros: no order ever has a wrong or empty region.
  - Cons: a gap in the mapping blocks real sales at checkout.
- **C. Store the raw country code**
  - Pros: no information lost.
  - Cons: the column then mixes two kinds of values, and the report has to tell them apart.

**Recommendation:** A (leaning). The strongest case for B is that tax data must be right. But losing sales over a gap in a lookup table costs more, and an `'UNKNOWN'` count is easy to monitor.

---

### Question 2: For old orders, is the customer's current country good enough?

**Context.** The only source is `customers.billing_country`, which holds today's value. I can't check how often customers change it. That's a fact about your data, and it's the fact this answer rests on.

**Example (illustrative):** a customer ordered in March while billing in Germany, then moved to Canada in June. Filling from the current country labels the March order as North America instead of EU.

**Options:**
- **A. Use the current country**
  - Pros: it's simple and needs only data we have.
  - Cons: orders from customers who moved get the wrong region, and the tax report could be wrong without anyone noticing.
- **B. Use the country at order time from another source** (e.g. stored invoices)
  - Pros: correct for tax.
  - Cons: no such source exists in this repo; it needs a system I haven't seen and may not be ready by Dec 1.

**Recommendation:** A (leaning), unless your tax team says old orders must reflect the country at order time, or you know moves are common. Either of those would switch me to B.

---

### Question 3: How should the change roll out?

**Context.** Whatever the approach, old orders must be filled in small batches by a separate script outside the deploy job, so no single step hits the 10-minute limit or the replica alarm. The open question is how to get to "required" safely.

**Options:**
- **A. (new) Add the column as required, with `'UNKNOWN'` as the default value**
  - How: add the column, update the app to write the real region on new orders, run the batch fill, then remove the default. On Postgres 15, adding a column with a fixed default doesn't rewrite the table, so it's instant.
  - Pros: three short steps; the column is required from day one.
  - Cons: "required" no longer proves the fill finished, since leftover placeholder rows also pass. It also depends on choosing A in Question 1.
- **B. Add the column as optional, then make it required later** (my original plan)
  - How: add the column with no default, update the app, run the batch fill, add a check that existing rows are filled (it doesn't block writes), then make the column required.
  - Pros: making the column required proves every row has a real region.
  - Cons: five steps over several deploys, and the check reads all 40M rows.

**Recommendation:** A (leaning). I changed this from my first answer because Postgres 15 adds a column with a fixed default without rewriting the table, which makes the extra steps of B unnecessary. B's strongest point, proof that the fill is complete, can be had with a quick count of `'UNKNOWN'` rows before Dec 1.

---

**The questions:**
1. For countries not in the mapping, should we store `'UNKNOWN'`, reject the order, or store the raw country code? And where do the region values come from?
2. For existing orders, is the customer's current billing country acceptable, or does tax need the country at the time of the order?
3. Should we add the column as required with an `'UNKNOWN'` default, or add it as optional and make it required in later steps?
