Here's the short version.

**The problem:** One ticket (PLAT-412) fixes a part of the system that another project (ADR-7) is about to stop using for checkout.

- **PLAT-412:** Make the Redis session storage more robust so it can't take checkout down again, like it did in the 47-minute outage on Oct 3. Cost: **8 days**.
- **ADR-7:** Already approved and due Dec 15. It moves checkout off Redis entirely and onto Postgres. Cost: **6 days**.

Once ADR-7 is done, checkout no longer touches Redis, so the outage can't happen to checkout that way anymore. PLAT-412 would then mostly protect the admin panel, which is the only thing still using Redis.

**The budget:** You have **10 days**. Both projects plus the small alerts ticket (PLAT-415, 2 days) add up to **16**, so something has to give.

**The question:** Which do you want this sprint?

1. **ADR-7 + alerts (8 days).** This fixes the outage risk by moving checkout off Redis, and it leaves 2 days spare. I recommend this one.
2. **PLAT-412 + alerts (10 days).** This hardens Redis, but ADR-7 then slips, which puts Dec 15 at risk.
3. **ADR-7 is being handled by someone else or out of a separate budget.** If so, tell me, because then the plan looks different.

**One smaller question:** RFC-3 would tighten the uptime target from 99.5% to 99.9%. That's roughly 43 minutes of allowed downtime a month instead of about 3.6 hours. It hasn't been approved yet. Should I plan around the stricter target or the current one?
