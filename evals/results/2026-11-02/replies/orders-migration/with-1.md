I'll go through them one at a time in plain terms.

**What we're doing:** adding a `region` column to every order, worked out from the customer's billing country (e.g. `DE`). The tax report needs it by Dec 1 (ticket TAX-19). Nothing is written yet. I need three answers first.

---

### 1. Which country goes in which region?

**Context:** a comment in `app/orders.py` says the country is turned into a region using a list called `REGIONS`. That list doesn't exist anywhere in this repo, so I don't know the region names or which countries belong to each.

**Options** for a country that isn't on the list:
- **A. Save the order with region `UNKNOWN`.**
  - Pros: an odd country never blocks a customer from ordering.
  - Cons: the tax report quietly gets bad data, and nobody notices unless they look.
- **B. Refuse the order.**
  - Pros: every saved order has a real region.
  - Cons: real customers can't check out until someone adds their country to the list.

**Recommendation:** A, leaning. A missed sale costs more than a fixable report row, and `UNKNOWN` rows are easy to search for later. B wins only if tax rules forbid an order with no known region.

**Question:** where is the country-to-region list, or what should it contain? And for a country that isn't on it, should we save it as `UNKNOWN` (A) or refuse the order (B)?

---

### 2. Old orders: which country do we use?

**Context:** about 40 million existing orders need a region. The database stores only each customer's *current* billing country, with no record of past addresses. So if a customer has moved, their old orders get the new country.

**Example:** a customer ordered in March while billed in Germany, then moved to the US in June.

| Option | Region on the March order |
|---|---|
| A. Use current country | US region (wrong for that order) |
| B. Use country at time of order | EU region (correct, but needs data we don't have) |

**Options:**
- **A. Use the current country.**
  - Pros: it's the only data we have, so it can be done now.
  - Cons: old orders from customers who moved get the wrong region, and the tax report shows them under the wrong place.
- **B. Use the country at the time of the order.**
  - Pros: tax figures are correct.
  - Cons: we'd need another data source, such as invoices or payment records, and none exists in this repo.

**Recommendation:** close call. A is the only option possible with what's here. B is right if tax has to reflect where the customer was when they ordered. That's a tax-rules question, so you or the tax team decide.

**Question:** is the current country good enough for old orders (A)? Or do they need the country at the time of the order (B), and if so, where does that data live?

---

### 3. Is it OK to do this in several steps?

**Context:** the simple approach is one change that adds the column and fills all 40M rows at once. That would take well over 10 minutes. Deploys are cut off at 10 minutes (DEPLOY-3), and a long table update last month blocked writes for 6 minutes and caused an outage (INC-212).

**Options:**
- **A. Several small steps.** Add an empty column, which is instant. Make new orders fill it. Fill old orders in small batches with a separate script outside the deploy. Then make the column required.
  - Pros: no downtime, no deploy timeout.
  - Cons: takes several deploys plus a script someone has to run and watch.
- **B. Do it all at once in a maintenance window.**
  - Pros: one change, simple to follow.
  - Cons: the site can't take orders for the duration, and it still has to happen outside the normal 10-minute deploy.

**Recommendation:** A, firm. B means planned downtime on a table that takes about 25,000 orders an hour at peak, and A avoids it. The report can treat missing regions as "unknown" until Dec 1, so the batches don't have to be fast.

**Question:** OK to do it in several steps with a separate fill-in script (A), or would you rather schedule a maintenance window (B)?
