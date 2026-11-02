Here are the same three questions in simpler terms.

**Context (applies to all three)**

Every order needs a new `region` field, and it can never be empty. The region comes from the country on the customer's billing address. The tax report (ticket TAX-19) needs it by Dec 1, a month from today. Until then the report can show orders without a region as "unknown". I haven't written anything yet. These three answers decide how I write it.

Two facts about your setup affect the answers. Both come from `OPS.md` and `db/schema.sql`:
- The `orders` table is large: about 40 million rows, with about 25,000 new orders an hour at peak.
- Database changes run inside the deploy job, which is killed after 10 minutes (ticket DEPLOY-3). Last month a 6-minute rewrite of the `payments` table blocked writes and caused an outage (INC-212).

---

### Question 1: Turning a country into a region

The code has a note (`app/orders.py:2`) saying the region is the billing country "mapped through `REGIONS`", meaning a lookup from country to region. The repo has only three files, and none of them defines `REGIONS`. So I don't know what the regions are (`EU`/`NA`/`APAC`? tax zones?) or where that lookup lives.

There's also a second part: what should happen to an order whose country isn't in the lookup?

**Options**
- **A. Save it with region `UNKNOWN`**
  - Pros: a customer can't be blocked from buying because a country is missing from the lookup.
  - Pros: the report already accepts "unknown".
  - Cons: those orders quietly get the wrong tax treatment until someone notices and fixes them.
- **B. Refuse the order**
  - Pros: no order is ever saved without a real region.
  - Cons: a missing entry in the lookup stops real customers from paying.

**Recommendation:** A, but I'm leaning rather than firm. B's argument is that bad tax data costs more than a lost sale. It doesn't win here because the report already accepts "unknown", while a failed checkout is lost money you can't recover.

**Question:** Where is the `REGIONS` lookup, or what should the regions be? And should an order from an unlisted country be saved as `UNKNOWN` or refused?

---

### Question 2: Old orders and customers who moved

To fill in the 40M existing orders, I'd use each customer's billing country as it is **today**. That's the only country the database stores. Orders don't store their own country, and the repo has no history of address changes.

**Example:** a customer billed in Germany in 2024 who later moved to the US. Their 2024 order would get the US region, even though it was a German sale when it happened.

**Options**
- **A. Use today's billing country for all old orders**
  - Pros: simple, and every old order gets a region.
  - Cons: orders from customers who moved get the wrong region, and nothing marks them as wrong.
- **B. Mark old orders `UNKNOWN`; only new orders get a real region**
  - Pros: no record claims something false.
  - Cons: the tax report has no usable region for all past orders.
- **C. Use another source of order-time country (billing system, invoices) if one exists**
  - Pros: correct values.
  - Cons: more work, and I don't know whether such a source exists.

**Recommendation:** A, but it's a close call. It rests on something I can't check from the repo: whether tax needs the country **at the time of the order**. If it does, A produces wrong tax data, and C, or B as a fallback, is the right choice.

**Question:** Is today's billing country good enough for old orders? If not, is there a record of each order's country at the time of purchase?

---

### Question 3: How to roll it out safely

Doing everything in one step (add the field, fill 40M rows, make it required) would very likely take longer than the 10-minute deploy limit. It would also block writes the way the `payments` change did in INC-212.

**Options**
- **A. Five small steps**
  1. Add the field as optional. This is instant.
  2. The app fills it in for new orders.
  3. A separate script fills old orders in small batches, outside the deploy, pausing whenever the backup database falls behind.
  4. Check that no order is missing a region. Postgres can do this check without blocking writes.
  5. Make the field required. This is quick because step 4 already checked every row.
  - Pros: no blocked writes, and no deploy timeouts.
  - Cons: several deploys plus a script someone has to run and watch, which takes days.
- **B. Do it all at once in a maintenance window, with the site paused**
  - Pros: one simple change.
  - Cons: real downtime for a 25k-orders-an-hour system.
  - Cons: it still needs a way to run longer than the deploy's 10 minutes.

**Recommendation:** A, firm. The 10-minute deploy limit and the INC-212 outage rule out a single large change during normal operation.

**Question:** Are you OK with the five-step rollout, including a separate fill-in script that someone runs and watches?
