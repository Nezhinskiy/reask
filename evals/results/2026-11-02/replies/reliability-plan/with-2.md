I'm asking two things before I plan the sprint's reliability work. The plan depends on the answers.

## Question 1: Which work goes into this sprint?

**Context.** You have 10 dev-days across two engineers. Three items compete for them:

- **PLAT-412** (8 days): move the session store from Redis Sentinel to Redis Cluster. Sentinel has a single primary server, and that primary caused **INC-301**, a 47-minute checkout outage on Oct 3. Cluster has no single primary.
- **PLAT-415** (2 days): add alerts when an endpoint's p99 latency gets too high. p99 is the speed of the slowest 1% of requests.
- **ADR-7** (6 days left): an accepted decision to retire checkout v1 by Dec 15. Checkout v2 keeps sessions in Postgres instead of Redis. Once it's done, only the admin panel uses Redis for sessions.

All three add up to 16 days, which is 6 more than you have. ADR-7 also makes PLAT-412 much less useful, because once checkout is off Redis, hardening Redis mainly protects the admin panel.

**Decided:** ADR-7 is accepted and due Dec 15.
**My assumption:** ADR-7's 6 days come out of these same 10 days. The docs don't say who does that work.

**Options**

- **A. ADR-7 + PLAT-415 (8 days, 2 spare)**
  - Pros: takes checkout off Redis, which removes INC-301's cause for checkout. It's also faster than PLAT-412 (6 days vs 8).
  - Pros: keeps the Dec 15 date on track.
  - Cons: the admin panel stays on Redis Sentinel with its single primary.
  - Cons: the docs don't say how Postgres is set up. If it also runs on one primary, checkout moves to a different single point of failure.
- **B. PLAT-412 + PLAT-415 (10 days)**
  - Pros: attacks the exact component that failed in INC-301.
  - Cons: 8 days spent on infrastructure that checkout stops using once ADR-7 ships.
  - Cons: no ADR-7 work this sprint, so Dec 15 is at risk.
- **C. ADR-7 is staffed separately**
  - If someone else does ADR-7, you have all 10 days. The real question then becomes whether PLAT-412 is worth 8 days just to protect the admin panel.

**Recommendation:** A, leaning. It removes the cause of INC-301 from checkout sooner and doesn't waste 8 days. The strongest argument against it is that B fixes the failure directly. But that fix stops mattering for checkout once ADR-7 lands. Two things would change my mind: ADR-7 being staffed separately (option C), or Postgres having the same single-primary weakness.

**Which do you want: A, B, or C?**

## Question 2: Which availability target should I plan against?

**Context.** Checkout's availability target, or SLO, is 99.5% today. That allows about 3.6 hours of downtime a month. **RFC-3** proposes raising it to 99.9%, which allows about 43 minutes. That's less than INC-301's 47 minutes, so one outage like it would use up the whole month. RFC-3 is still a draft waiting for sign-off from the head of product.

The target affects how hard I push on reliability items and what I put in A's 2 spare days. It doesn't change the answer to Question 1.

**Options**

- **99.5% (current)**
  - Pros: it's the target in force today.
  - Cons: the plan may fall short if RFC-3 is approved mid-sprint.
- **99.9% (proposed)**
  - Pros: prepares for where things are likely headed.
  - Cons: commits capacity to a target nobody has approved.

**Recommendation:** 99.5%, firm, because RFC-3 isn't signed off. I'd note 99.9% as a stretch goal.

**Should I plan against 99.5% or 99.9%?**
