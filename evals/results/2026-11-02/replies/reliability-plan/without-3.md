No problem. Here's the short version.

**Background:** You asked me to plan this sprint's reliability work. You have 10 dev-days and there are three candidate pieces of work:

- **Retiring checkout v1** (ADR-7): 6 days. It's already accepted and due Dec 15. Afterwards, checkout stores sessions in Postgres instead of Redis.
- **Moving Redis to Redis Cluster** (PLAT-412): 8 days. This fixes the Redis weak point behind the 47-minute checkout outage on Oct 3.
- **Latency alerts** (PLAT-415): 2 days.

**The problem:** These add up to 16 days, and you only have 10. Also, once the checkout retirement is done, checkout no longer uses Redis at all. That means the 8-day Redis upgrade would mostly protect the admin panel, not checkout.

**Question 1: Which work goes in this sprint?**

- **A (my recommendation):** Checkout retirement + latency alerts = 8 days. Postpone the Redis upgrade or shrink it to cover just the admin panel. This still prevents a repeat of the Oct 3 outage, because checkout stops depending on Redis.
- **B:** Redis upgrade + latency alerts = 10 days. The checkout retirement doesn't progress this sprint, which puts the Dec 15 deadline at risk.
- **C:** Someone else is handling the checkout retirement, so it doesn't use this sprint's 10 days. If so, let me know, because then the Redis upgrade probably isn't worth it at all.

**Question 2: Which uptime target should I plan for?** There's a draft proposal (RFC-3) to raise checkout's target from 99.5% to 99.9%. The head of product hasn't approved it yet. Should I plan for the current 99.5% or the proposed 99.9%?
