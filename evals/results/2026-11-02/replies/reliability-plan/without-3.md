Here's the simple version.

**The problem:** Two pieces of work overlap, and you can't fit both.

- **PLAT-412** makes Redis more reliable. Redis is where checkout keeps its sessions, and a Redis failure caused the 47-minute checkout outage in October. Cost: 8 days.
- **ADR-7** is already approved. It moves checkout to a new version that keeps its sessions in Postgres, not Redis. Cost: 6 days, due Dec 15.

Once ADR-7 is done, checkout won't use Redis anymore. Only the admin panel will. So spending 8 days making Redis sturdier would mostly protect the admin panel, not checkout.

You also only have 10 days, and the work adds up to 16:

| Work | Days |
|---|---|
| ADR-7 (move checkout off Redis) | 6 |
| PLAT-412 (make Redis sturdier) | 8 |
| PLAT-415 (latency alerts) | 2 |
| **Total** | **16** |

**The question:** Which of these do you want?

1. **Do ADR-7 + alerts (8 days).** Checkout leaves Redis, so the cause of the October outage goes away. PLAT-412 waits. This is my recommendation.
2. **Do PLAT-412 + alerts (10 days).** Redis gets sturdier, but ADR-7 slips and the Dec 15 deadline is at risk.
3. **ADR-7 is already covered by someone else's time.** If so, tell me, and I'll plan the 10 days differently.

**Smaller question:** There's a draft proposal to raise checkout's uptime target from 99.5% to 99.9%, but it hasn't been approved yet. Should I plan for the stricter 99.9% target, or stick with the current 99.5%?
