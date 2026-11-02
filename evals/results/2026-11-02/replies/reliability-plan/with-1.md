Here's the question again, in simpler terms. I'm asking two things.

## Question 1: Where do the 10 dev-days go?

**Context.** This sprint you have 10 dev-days (two engineers) for reliability work. On Oct 3, checkout went down for 47 minutes (INC-301). The cause was the Redis server that stores user sessions: it has a single main server, and when that server failed, checkout failed with it. There are two pieces of work that deal with this, and they overlap:

- **PLAT-412** (8 days) rebuilds that Redis setup so it no longer depends on one main server. It fixes the cause directly.
- **ADR-7** is a decision your team already accepted. By Dec 15, the old checkout gets replaced by checkout v2, which stores sessions in Postgres (a different database) and doesn't use Redis. It has 6 days of work left. Once it's done, the only thing still using Redis sessions is the admin panel.

So if ADR-7 ships, checkout no longer depends on Redis at all, and PLAT-412 would only protect the admin panel. There's also a small ticket, **PLAT-415** (2 days): latency alerts for every endpoint.

**My assumption:** I don't know whether ADR-7's remaining 6 days come out of these 10 days or out of some other budget. The answer changes the options.

**Live example:**

| | Days used | Checkout still depends on Redis? | Risk to Dec 15 |
|---|---|---|---|
| A: ADR-7 + alerts | 8 of 10 | No, once ADR-7 ships | On track |
| B: PLAT-412 + alerts | 10 of 10 | Yes, but Redis no longer has a single point of failure | ADR-7 doesn't move this sprint |
| All three | 16 of 10 | — | Doesn't fit |

**Options**

- **A. Do ADR-7 and the alerts. Postpone PLAT-412 or cut it down to the admin panel.**
  - Pros: removes checkout's dependence on Redis for good, keeps the Dec 15 date, and leaves 2 days spare.
  - Cons: until ADR-7 ships, checkout still sits on the Redis setup that broke on Oct 3. Also, I don't know whether checkout v2's Postgres has its own single main server, so the same kind of outage might just move there.
- **B. Do PLAT-412 and the alerts.**
  - Pros: fixes the exact cause of the Oct 3 outage right away.
  - Cons: 8 days spent hardening something checkout stops using a few weeks later. ADR-7 doesn't move this sprint, so Dec 15 gets tighter.
- **C. ADR-7 is paid for from a different budget.** Then the 10 days only cover PLAT-412 and the alerts, and the real question is whether PLAT-412 is still worth 8 days if checkout leaves Redis by Dec 15.

**Recommendation:** A, though I'm leaning, not certain. The strongest argument for B is that it fixes the known cause immediately. It doesn't win because ADR-7 already makes that fix mostly unnecessary for checkout, at a lower cost. One thing would change my mind: if checkout v2's Postgres has the same single-server weakness, the Redis work might still matter for comparison.

**Which do you want this sprint: A, B, or C (ADR-7 is funded elsewhere)?**

## Question 2: Which uptime target should the plan aim for?

**Context.** Checkout currently promises 99.5% uptime, which allows about 3.6 hours of downtime a month. A draft proposal, RFC-3, would raise that to 99.9%, which allows about 43 minutes a month. The Oct 3 outage alone (47 minutes) would have used up all of that. The head of product hasn't signed off on RFC-3 yet.

**Options**

- **Plan against 99.5% (the current target).**
  - Pros: it's the only target actually approved.
  - Cons: if RFC-3 gets approved mid-sprint, the plan may look too relaxed.
- **Plan against 99.9%.**
  - Pros: ready if RFC-3 is approved.
  - Cons: it plans around a target nobody has approved yet.

**Recommendation:** 99.5%, and I'm confident about this one, because RFC-3 is still a draft. Either way it barely changes the plan, since A is my pick under both targets.

**Which target should I use: 99.5% or 99.9%?**
