No problem. I need you to decide one thing before I can plan the sprint.

**The question:** Should this sprint go to finishing the checkout v2 migration (ADR-7), or to moving the Redis session store to Redis Cluster (PLAT-412)? We don't have room for both.

**Why it matters:**
- The Oct 3 checkout outage (INC-301, 47 minutes) happened because the Redis session store has a single primary. PLAT-412 fixes that by moving to Redis Cluster, at a cost of 8 dev-days.
- ADR-7 is already accepted and due Dec 15. It moves checkout sessions out of Redis and into Postgres, with 6 dev-days of work left. Once it's done, only the admin panel still uses Redis sessions, so PLAT-412 would mostly be protecting the admin panel, not checkout.
- You have 10 dev-days. ADR-7 (6) + PLAT-412 (8) + the latency alerts ticket PLAT-415 (2) comes to 16.

**Your options:**
- **A (my recommendation):** Finish ADR-7 and do PLAT-415. That's 8 days with 2 left over. Checkout leaves Redis, which removes the cause of the outage. PLAT-412 is postponed or reduced to cover just the admin panel.
- **B:** Do PLAT-412 and PLAT-415, which uses all 10 days. ADR-7 stalls this sprint, which puts the Dec 15 date at risk.
- **C:** ADR-7 is staffed separately and doesn't use this sprint's capacity. If so, tell me, because then we'd need to decide whether PLAT-412 is still worth doing.

**A second, smaller question:** There's a draft proposal (RFC-3) to raise checkout's availability target from 99.5% to 99.9%, but the head of product hasn't signed off on it. Should I plan against 99.9% or the current 99.5%?
