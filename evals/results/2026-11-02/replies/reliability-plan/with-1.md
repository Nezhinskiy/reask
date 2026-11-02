I'm waiting on two decisions before I can plan this sprint's reliability work.

**Context:** There's room for 10 dev-days this sprint (two engineers). Three pieces of work compete for it, and together they need 16 days:

- **PLAT-412** (8 days): moves the checkout session store from Redis Sentinel to Redis Cluster. The session store is where logged-in shoppers' checkout state lives. Sentinel runs one primary server, and when it failed on Oct 3 checkout went down for 47 minutes (incident INC-301). Cluster has no single primary like that.
- **PLAT-415** (2 days): adds alerts when an endpoint's p99 latency (the response time the slowest 1% of requests exceed) gets too high.
- **ADR-7** (6 days left): an accepted decision to retire checkout v1 by Dec 15. Checkout v2 keeps sessions in Postgres, not Redis. Once this ships, checkout no longer uses Redis at all, and only the admin panel still keeps sessions there.

**Decided:** ADR-7 is accepted with a Dec 15 deadline.
**My assumption:** ADR-7's remaining 6 days come out of this team's 10. Nothing in docs/ confirms who owns it, and the answer would change my recommendation.

**The core tension:** PLAT-412 and ADR-7 both remove the failure behind INC-301, but in different ways. PLAT-412 makes Redis more reliable. ADR-7 takes checkout off Redis entirely. Doing both means 8 days spent hardening a store that checkout leaves about six weeks later.

| | Days used (of 10) | Checkout still depends on one Redis primary? | Dec 15 deadline |
|---|---|---|---|
| A: ADR-7 + PLAT-415 | 8 (2 spare) | No, once ADR-7 ships | On track |
| B: PLAT-412 + PLAT-415 | 10 | No, after the migration | 6 days still to find in later sprints |
| C: ADR-7 is staffed elsewhere | depends | depends | n/a here |

## Question 1: What goes into this sprint?

**A. ADR-7 + PLAT-415, and defer PLAT-412 or shrink it to the admin panel**
- Pros: removes the INC-301 risk for checkout permanently. Keeps Dec 15 on track. Leaves 2 days of slack.
- Cons: checkout stays on single-primary Redis until ADR-7 cuts over, so an INC-301 repeat is possible in the meantime. The admin panel stays on Sentinel.

**B. PLAT-412 + PLAT-415**
- Pros: goes straight at INC-301's cause and uses exactly 10 days.
- Cons: about 8 days on infrastructure checkout abandons by Dec 15, so what lasts mostly protects the admin panel. ADR-7's 6 days get pushed into the remaining weeks.

**C. ADR-7 doesn't come from this team's capacity**
- Then the choice is PLAT-412 + PLAT-415 against PLAT-415 alone. PLAT-412 still loses most of its value once ADR-7 ships, whoever does ADR-7.

**Recommendation: A, leaning.** The deciding fact is that ADR-7 removes checkout's dependence on Redis, which makes most of PLAT-412 temporary. The best case for B is that it protects checkout sooner than ADR-7 would. It doesn't win because ADR-7 fits in this sprint too. If ADR-7 isn't this team's work (option C), my recommendation changes.

## Question 2: Which availability target should the plan aim for?

**Context:** Checkout's current SLO (the availability target it's measured against) is 99.5%, which allows about 3.6 hours of downtime a month. RFC-3 proposes raising it to 99.9%, about 43 minutes a month. INC-301 alone would have used up that whole budget. RFC-3 is still a draft and needs the head of product's sign-off.

- **Current 99.5%:** Pros: it's the approved target. Cons: we might under-invest if 99.9% gets approved during the sprint.
- **Proposed 99.9%:** Pros: gets ahead of where the target is probably heading. Cons: it isn't approved, and it would raise the priority of anything that cuts outage minutes.

**Recommendation: 99.5%, firm.** It's the only approved target. Under either target, option A still ranks first.

---

**Your answers:** (1) A, B, or C? If C, who owns ADR-7? (2) Plan against 99.5% or 99.9%?
