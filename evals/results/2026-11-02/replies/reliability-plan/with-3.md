I asked two things. Here they are again, in plain terms.

## Shared context

**The goal:** pick the reliability work for this sprint. You have **10 dev-days** (two engineers).

**What happened:** on Oct 3, checkout was down for 47 minutes (incident INC-301). Checkout keeps each shopper's session (who they are, what's in their cart) in Redis, an in-memory database. Our Redis setup has one main server, and when that server failed, checkout went down with it.

**The work on the table:**

| Item | What it is | Cost |
|---|---|---|
| **PLAT-412** | Rebuild the Redis session store so it has no single main server. This fixes the INC-301 cause directly. | 8 days |
| **PLAT-415** | Alerts when any endpoint gets slow (p99 latency, meaning the slowest 1% of requests) | 2 days |
| **ADR-7** | An already-approved decision to shut down the old checkout (v1) by **Dec 15** and move all traffic to checkout v2, which keeps sessions in **Postgres, not Redis**. 6 days of work left. | 6 days |

All three add up to 16 days, which is more than the 10 you have.

**The catch:** once ADR-7 is done, checkout stops using Redis for sessions. Only the admin panel still would. So the 8 days spent on PLAT-412 would mostly protect the admin panel, not checkout.

**My assumptions (not confirmed):** that ADR-7's 6 days have to come out of these same 10 days, and that checkout v2's Postgres doesn't have the same single-server weakness. Nothing in docs/ settles either one.

## Question 1: What goes into the sprint?

**A. ADR-7 + PLAT-415** (8 days, 2 left over)
- Pros: takes checkout off Redis completely, so an INC-301-style outage can't take checkout down. Keeps the Dec 15 deadline on track. Adds the alerts.
- Cons: checkout stays on the fragile Redis setup until ADR-7 actually ships. If Postgres also runs on a single main server, we've swapped one weak point for another.

**B. PLAT-412 + PLAT-415** (10 days)
- Pros: fixes exactly what broke on Oct 3 and makes Redis sturdier.
- Cons: about 8 days of work that loses most of its value by Dec 15. ADR-7 gets no time this sprint, which puts the deadline at risk.

**C. ADR-7 is someone else's work** (it doesn't come out of these 10 days)
- Then all 10 days are free, and the question becomes whether PLAT-412 is worth 8 days for the admin panel alone.

**Recommendation: A, leaning.** The strongest case for B is that it fixes the known cause right away. It still loses to A because ADR-7 is already approved and removes checkout from Redis altogether. That makes the Redis rebuild mostly wasted for checkout. Two things would change my mind: Postgres turning out to have the same single-server weakness, or ADR-7 being staffed outside this sprint.

## Question 2: Which uptime target should the plan aim for?

Checkout's current official target (SLO) is 99.5% uptime, which allows about 3.6 hours of downtime a month. A draft proposal, RFC-3, would raise it to 99.9%, which allows only about 43 minutes. Under 99.9%, the Oct 3 outage alone (47 minutes) would have blown the whole month's allowance. RFC-3 hasn't been approved yet; it needs sign-off from the head of product.

- **Current 99.5%:** Pros: it's the official target. Cons: if RFC-3 is approved mid-sprint, the plan may be aiming too low.
- **Proposed 99.9%:** Pros: gets ahead of a likely change. Cons: commits the team to a target nobody has approved.

**Recommendation: 99.5%, leaning.** It's the only target that's actually agreed. Option A from Question 1 is the right pick under either target. A stricter target would just make it more urgent to get checkout off Redis.

---

**Do you want A, B, or C for the sprint? And should I plan against 99.5% or 99.9%?** If C, tell me who owns ADR-7.
