I'm asking two things: how to spend this sprint's 10 days, and which uptime target to plan against.

**Context:** You asked me to plan this sprint's reliability work using the four files in `docs/`. I haven't written the plan yet because the files conflict:

- **Capacity:** 10 dev-days, two engineers (`team.md`).
- **PLAT-412** (8 days): move the session store from Redis Sentinel to Redis Cluster. Today one Redis primary server holds the sessions. When it failed on Oct 3, checkout was down for 47 minutes (INC-301). Cluster removes that single point of failure.
- **PLAT-415** (2 days): add p99 latency alerts for each endpoint. These fire when the slowest 1% of requests get too slow.
- **ADR-7** (accepted, 6 days of work left, due Dec 15): retire checkout v1. Checkout v2 keeps sessions in Postgres, not Redis. After ADR-7 ships, only the admin panel uses Redis sessions.

**The conflict:** PLAT-412 hardens Redis for checkout, but ADR-7 moves checkout off Redis. Doing all three takes 6 + 8 + 2 = 16 days, and you have 10.

**My assumption, not confirmed:** ADR-7's 6 days come out of this same 10-day budget. The docs don't say who does that work.

## Question 1: What goes into the sprint?

| | ADR-7 | PLAT-412 | PLAT-415 | Days |
|---|---|---|---|---|
| A | ✓ | deferred, or cut to admin panel only | ✓ | 8 |
| B | — | ✓ | ✓ | 10 |
| C | another team does it | your call | ✓ | ≤10 |

**A. ADR-7 + PLAT-415**
- Pros: Checkout no longer depends on Redis at all, so the INC-301 failure can't hit checkout again. Keeps Dec 15 on track. Leaves 2 days spare.
- Cons: Until ADR-7 ships, checkout still runs on the single Redis primary, and a repeat of INC-301 in that window has no fix. The admin panel stays on Sentinel.

**B. PLAT-412 + PLAT-415**
- Pros: Fixes the exact cause of INC-301 for every Redis user, admin panel included.
- Cons: Spends 8 days hardening a store that checkout leaves weeks later. ADR-7 doesn't move, which puts Dec 15 at risk.

**C. ADR-7 isn't on this budget**
- Pros: If true, all 10 days go to PLAT-412 and PLAT-415.
- Cons: PLAT-412 would still mostly protect the admin panel once ADR-7 ships, so it may not be worth 8 days.

**Recommendation: A, leaning.** ADR-7 itself says checkout leaves Redis, so PLAT-412's main benefit disappears when ADR-7 ships. The strongest case for B is the risk window before ADR-7 is done. It doesn't win, because PLAT-412 also takes most of the sprint to land, so it shortens that window very little. If ADR-7 is staffed separately (C), I'd look at this again.

**Which do you want: A, B, or C?**

## Question 2: Which uptime target should the plan assume?

**Context:** Checkout's availability target (SLO) is currently 99.5%, which allows about 3.6 hours of downtime a month. RFC-3, still a draft that needs the head of product's sign-off, proposes 99.9%, about 43 minutes a month. INC-301 alone (47 minutes) would have used up the whole 99.9% budget.

**Options:**
- **Keep 99.5%.** Pros: it's the approved target. Cons: it may understate how urgent the work is if RFC-3 gets approved.
- **Plan for 99.9%.** Pros: it gets ahead of the likely new target. Cons: it commits work to a target nobody has approved.

**Recommendation: keep 99.5%, firm.** It's the only target that has been approved, and it doesn't change the answer to Question 1 either way.

**Should I plan against 99.5% or 99.9%?**
