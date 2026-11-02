# heldout-b, cell B

## Run 1

all-decisions FAIL, decision-1 FAIL, decision-2 PASS, facts PASS, no-trap-pick PASS, references PASS; 582 words

No files changed. Here's the decision again, in plain terms.

**Context**

Tonight (22:00–23:00 UTC) we move api.stagelark.example from the old data centre (old-dc) to the new Kubernetes cluster (k-east). Your rule is that "the bungee", sending traffic back to old-dc if k-east misbehaves, must work within 15 minutes. Nothing can start until we pick a plan.

The written plan (`docs/CUTOVER.md`) changes the DNS record from old-dc's address (203.0.113.10) to k-east's (198.51.100.24), and changes it back to bungee. The catch is the record's TTL, which is how long phones, browsers and ISPs may keep a saved answer before asking again. In the 30 Oct zone export it's 86400 seconds, one day. Anyone who has already picked up k-east's address can stay on k-east for up to 24 hours after we switch back. I can't see the live DNS console. If someone lowered the TTL to about 5 minutes before 22:00 yesterday, the written plan is fine.

**Example:** a phone looks up the API at 22:05 tonight. k-east starts failing at 22:20, and we bungee at 22:25.

| Plan | When that phone is back on old-dc |
|---|---|
| Written plan, TTL still one day | Up to 22:05 tomorrow |
| Written plan, TTL already 5 min | About 22:30 |
| A (switch at old-dc's load balancer) | 22:25, seconds after we act |
| B (postpone) | Doesn't apply: nothing moves tonight |

**Options**

- **A. Switch at old-dc's load balancer tonight.** The DNS record stays on old-dc. We change old-dc's HAProxy (the program that passes incoming requests to the servers) so it sends requests to k-east instead of the three old servers. To bungee, we change it back.
  - Pros: bungee takes seconds for everyone. The window happens as announced.
  - Cons: the HAProxy-to-k-east route has never carried real traffic. The 72-hour shadow test used a separate mirroring tool, so tonight is its first real use, on an unreviewed config change. Each request gets about 34 ms slower. And old-dc stays the front door, so a DNS move is still needed before the lease ends on 30 Nov.
- **B. Do prep only tonight and move later.** Lower the TTL to 5 minutes now, scale up and check k-east, and do the DNS switch at least 24 hours later.
  - Pros: k-east serves directly, with no detour and no new HAProxy config. It's the plan as written, just with a short TTL.
  - Cons: we break a promise on the status page and announce a new window. The TTL has to stay low until old-dc is shut down.
- **C. Run the written plan unchanged.** This only meets the bungee rule if the live console shows a TTL of about 5 minutes that was set before 22:00 yesterday.

**Recommendation:** I lean towards A, because it's the only option that keeps tonight's window and meets the 15-minute rule. The strongest case against it is that the HAProxy-to-k-east route is untested, and B carries no new risk at all. A still wins if a check before 22:00 passes: from lb-1 (the old-dc load balancer machine), call k-east's `/healthz` over HTTPS with the name api.stagelark.example. If that check fails, or you'd rather not make a config change on the night, pick B.

**The question:** what TTL does the DNS console show for `api` right now, and do we run **A** (switch at the load balancer tonight), **B** (prep tonight, move later), or **C** (written plan, only if the TTL is already low)?

---

## Run 2

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts PASS, no-trap-pick PASS, references FAIL; 639 words

Here's the question again in plain words. I still haven't changed any files.

**Context**

Tonight (Mon 2 Nov, 22:00–23:00 UTC) the plan is to move `api.stagelark.example` from the old data centre (old-dc, address 203.0.113.10) to the new Kubernetes cluster (k-east, address 198.51.100.24). Both run the same app version against the same database. Only the place that answers requests changes.

- **Decided (by you):** the bungee, meaning the way back to old-dc, must work within 15 minutes.
- **The problem:** the runbook switches by editing the DNS record, and that record has a TTL of 86400 seconds. The TTL is how long computers on the internet may keep a remembered address before asking again, so 86400 means a full day. If k-east breaks after the switch, changing DNS back can take up to 24 hours to reach everyone. That fails the bungee.
- **My assumption:** the TTL is still 86400. My only source is a zone export from 30 Oct. Someone may have lowered it in the DNS provider's console since then.

**Example:** a user's phone looks up the address at 22:05. At 22:20, k-east starts failing.

| | Runbook as written | A: switch at old-dc's load balancer | B: postpone |
|---|---|---|---|
| Where the phone goes at 22:05 | k-east | old-dc, which forwards to k-east | old-dc |
| After you pull the bungee at 22:20 | Stuck on k-east until 22:05 Tuesday | Back on old-dc within seconds | Nothing to pull |

**Options**

**A. Switch tonight at old-dc's load balancer, HAProxy (the program on 203.0.113.10 that hands requests to the app servers).** DNS stays the same. At 22:00 we tell HAProxy to forward requests to k-east, and switching it back is the bungee. Tonight we also lower the DNS TTL to 5 minutes so DNS can move safely later.
- Pros: the bungee takes seconds for every user, and it fits tonight's announced window.
- Pros: the 72-hour test with copied live traffic showed k-east handling real traffic with no errors.
- Cons: it's a live change to the production load balancer that nobody reviewed for this window, and the runbook has to be rewritten tonight.
- Cons: HAProxy has never sent real requests to k-east this way. The test used a separate copying tool. So the encryption setup and hostname have to be right on the first try.
- Cons: traffic still passes through old-dc, adding 34 ms per request, until DNS moves later.

**B. Prepare tonight, switch later.** Tonight we lower the TTL to 5 minutes and get k-east ready. At least 24 hours later we switch DNS, and then changing DNS back is a bungee that takes about 5 minutes.
- Pros: no risky change to old-dc tonight, and the switch is the simple DNS edit the team already planned.
- Cons: it breaks the window announced on the status page. You'd need a new date, and the margin before the old-dc lease ends on 30 Nov gets smaller.
- Cons: the TTL has to stay low until old-dc is shut down. If someone raises it again to save money, the bungee breaks.

**Recommendation: A, leaning.** It's the only option that gives a working bungee inside tonight's window. The strongest argument against it is that it's an unreviewed change to the production load balancer. That doesn't outweigh it for me, because the old app servers stay in the config and undoing it takes one reload. If your team won't change HAProxy without a review, choose B.

**Questions**

1. In the DNS provider's console right now, what is the TTL on `api`: still 86400, or already about 300 (5 minutes)? If it was lowered before 22:00 yesterday, the original runbook works as written and you don't need to choose.
2. If it's still 86400: **A** (switch at HAProxy tonight) or **B** (postpone)?

---

## Run 3

all-decisions PASS, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 510 words

Here it is again, in plain words.

**Context.** Tonight (Mon 2 Nov, 22:00–23:00 UTC) the plan is to move `api.stagelark.example` from the old data centre (old-dc) to the new cluster (k-east). Both run the same app on the same database. You set one hard rule: if k-east misbehaves, sending users back to old-dc (the bungee) has to work within 15 minutes.

The written runbook moves users by changing the DNS address record from old-dc to k-east. The bungee in that plan is changing it back. But the record has a 24-hour cache time (TTL): devices that saw the new address may keep using it for up to a day. So the bungee could take 24 hours, not 15 minutes. **Decided:** the bungee has to work in 15 minutes. **My assumption:** the live DNS settings still show the 24-hour TTL from the 30 Oct export. If someone lowered it to about 5 minutes before 22:00 yesterday, the runbook works as written and none of this matters.

**Example: k-east starts failing at 22:20**

| | A: switch at old-dc's load balancer | B: postpone |
|---|---|---|
| Who is affected | Everyone, since all traffic goes through old-dc to k-east | Nobody, since k-east isn't live yet |
| Bungee | Point the load balancer back at old-dc's servers, done in seconds | Not needed tonight |

**Options**

**A. Switch tonight at old-dc's load balancer (HAProxy).** DNS stays the same. Old-dc's HAProxy starts passing requests to k-east, and for the bungee you flip it back.
- Pros: meets the 15 minutes easily; keeps tonight's announced window.
- Cons: that forwarding path has never carried real traffic, because the earlier test sent copies of traffic through a separate tool, not through HAProxy itself. It's an unreviewed change to the production load balancer during the window. Every request takes an extra 34 ms trip (k-east p95 goes from about 41 ms to about 75 ms, against 63 ms today). Old-dc stays in the path, so a DNS move is still needed before the lease ends on 30 Nov.

**B. Do only prep tonight and switch later.** Tonight, lower the TTL to 5 minutes and check k-east. Move DNS at least 24 hours later, with a 5-minute bungee.
- Pros: no untested path; it's the runbook you already reviewed, just on a later date; it ends in the final setup with no detour through old-dc.
- Cons: breaks the window you announced; needs a new status-page notice; the TTL has to stay low until old-dc is shut down.

**Recommendation: A, but only leaning.** It's the only option that both meets the 15 minutes and happens tonight. The strongest point against it is the untested forwarding path. It doesn't win because you can test that path at 21:50 before switching anyone, and if the test fails, you fall back to B.

**Questions**
1. Do we switch tonight at old-dc's load balancer (A), or do only prep tonight and switch later (B)?
2. In the live DNS settings, what TTL does the `api` record show right now?
