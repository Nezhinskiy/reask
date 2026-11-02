No problem, here's the question again.

**The situation:** You asked me to plan this sprint's reliability work. You have 10 dev-days, but the work in docs/ adds up to 16:

- **PLAT-412** (8 days): move the session store from Redis Sentinel to Redis Cluster. This is meant to prevent another INC-301, the 47-minute checkout outage on Oct 3.
- **PLAT-415** (2 days): add p99 latency alerts per endpoint.
- **ADR-7** (6 days left, due Dec 15): move checkout to v2, which stores sessions in Postgres instead of Redis.

**The catch:** Once ADR-7 is done, checkout no longer uses Redis at all. Only the admin panel does. So PLAT-412 would spend 8 days hardening Redis for something checkout is about to stop using.

**Question 1: Which work goes into this sprint?**

- **A (my recommendation):** ADR-7 + PLAT-415 = 8 days, with 2 to spare. Drop PLAT-412 or shrink it to just the admin panel. This prevents another INC-301 by moving checkout off Redis instead of hardening Redis.
- **B:** PLAT-412 + PLAT-415 = 10 days. ADR-7 gets no time this sprint, which puts the Dec 15 deadline at risk.
- **C:** ADR-7 comes out of a different team's or budget's time, not these 10 days. If so, let me know, and I'll reconsider whether PLAT-412 is worth doing at all.

**Question 2: Which uptime target should I plan for?**

A draft proposal (RFC-3) would raise checkout's target from 99.5% to 99.9%. That cuts the allowed downtime from about 3.6 hours a month to about 43 minutes. The head of product hasn't approved it yet. Should I plan for 99.9% anyway, or stick with the current 99.5%?

A short answer like "A, 99.5%" is all I need.
