Here are the same three questions in simpler terms.

**The setup.** You want a new `region` column on `orders` that is always filled in (NOT NULL). The tax report needs it by Dec 1, four weeks from today. Until then, reports can show a missing region as "unknown".

`orders` is big and busy: about 40 million rows, and up to about 25,000 new orders an hour. Database changes run inside the deploy job, which gets cut off after 10 minutes. Last month a 6-minute rewrite of the `payments` table stopped writes and caused an outage. So filling 40 million rows in one step during a deploy is risky.

Nothing has been written yet.

---

### Question 1: What exactly goes in `region`?

**Context.** The only hint is a comment in `app/orders.py`: region is "billing_country mapped through REGIONS". `REGIONS` doesn't exist in the repo. It's in no file I could see, and the repo has only three files. Billing country is a 2-letter code like `DE` or `US`.

**Options**
- **A. Store the country code itself** (`DE` stays `DE`). *New.*
  - Pros: nothing to maintain, and every order gets a valid value.
  - Cons: if the tax report needs groups like "EU", every report has to do the grouping itself.
- **B. Map countries to groups** (`DE` becomes `EU`), using a list you give me. A country that isn't on the list gets `UNKNOWN`.
  - Pros: matches the code comment, and the report gets the groups directly.
  - Cons: someone has to keep the list up to date, and a country missing from it gets labelled `UNKNOWN`, which shows up as unknown in the tax report.
- **C. Map as in B, but refuse to create an order whose country isn't on the list.**
  - Pros: no bad data, ever.
  - Cons: a missing list entry blocks real customers from ordering.

**Recommendation:** B, leaning. Grouping by region seems to be the intent, and the report already accepts "unknown". This depends on what tax actually needs: if TAX-19 wants plain countries, A is better.

---

### Question 2: Which country do old orders get?

**Context.** Old orders have to be filled in using the customer's billing country *as it is today*. The database keeps no history of past countries.

**Example:** a customer ordered in 2024 while living in Germany, then moved to the US in 2025. Their 2024 order would be labelled US.

**Options**
- **A. Use today's country.**
  - Pros: possible right now with the data we have.
  - Cons: orders from customers who have moved get the wrong region, and that error ends up in a tax report.
- **B. Use a historical source of the country at order time** (invoices, another system), if one exists.
  - Pros: correct.
  - Cons: I don't know if such a source exists. It isn't in this repo.

**Recommendation:** A, leaning, because B has no data source I can see. I can't check how many customers have moved. If tax needs the country at the time of the order, you'd need B.

---

### Question 3: How should the change roll out?

**Context.** The new column has to exist without locking the table for minutes. One useful fact: Postgres can add a column with a fixed default value instantly, without rewriting the table.

**Options**
- **A. Add it filled with `UNKNOWN`, then fill it in gradually.** *New.* Add the column as NOT NULL with default `UNKNOWN`, which is instant. The app then writes the real region on new orders. A separate script outside the deploy job fills old orders in small batches. Afterwards, remove the default.
  - Pros: three steps, and the column is never empty.
  - Cons: until the script finishes, `UNKNOWN` can mean either "not filled yet" or "country not on the list".
- **B. My earlier plan.** Add the column empty, fill it in gradually, then make it NOT NULL with a safe two-step check.
  - Pros: an empty value clearly means "not filled yet".
  - Cons: five steps and more chances to slip.
- **C. One step during a maintenance window.**
  - Pros: simplest.
  - Cons: orders stop for the length of the window, and it may not finish within the 10-minute deploy limit.

**Recommendation:** A, leaning. It replaces my earlier pick (B) because adding a column with a fixed default is instant, so the column can be NOT NULL from the start. B's advantage only matters while the fill-in script is running.

---

**Your answers:**
1. Should `region` hold the country code (A), a group from a list you'll give me (B), or a group with orders blocked for unlisted countries (C)?
2. Should old orders use today's country (A), or is there a source for the country at the time of the order (B)?
3. Should the rollout be: add filled with `UNKNOWN` and fill in gradually (A), add empty and enforce later (B), or one step in a maintenance window (C)?
