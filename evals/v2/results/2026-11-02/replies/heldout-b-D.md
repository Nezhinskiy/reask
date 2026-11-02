# heldout-b, cell D

## Run 1

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 825 words

I haven't changed any files. Here is everything you need to decide.

## Context

**What we're doing.** OPS-140 moves the public API, `api.stagelark.example`, from the old data centre (**old-dc**) to the new Kubernetes cluster (**k-east**). It's tonight, Mon 2 Nov, 22:00–23:00 UTC, and the window was announced on the status page last week. Both sites run the same app image (`stagelark-api:2026.10.29`) on the same database (`pg-main`), so no data moves. Only where requests are served from changes.

**Today.** DNS sends `api.stagelark.example` to **203.0.113.10**, old-dc's load balancer (HAProxy on `lb-1`). That balancer spreads requests over three app servers. k-east is ready behind its own address, **198.51.100.24**, but gets no live traffic. **OPS-133** (done) proved k-east can take the load: old-dc copied live traffic to it for 72 hours with no errors. Its p95 (the time 95% of requests finish within) was 41 ms against old-dc's 63 ms, and old-dc to k-east is 34 ms away. **OPS-141** shuts old-dc down after a week without a rollback. The lease ends 30 Nov.

**Decided (by you):** "the bungee" means pointing the API back at old-dc if k-east misbehaves, and it must take effect within 15 minutes.

**The problem.** The runbook (`docs/CUTOVER.md`) switches traffic by editing the DNS record, and does the bungee by editing it back. But the record has a **TTL** (how long other servers may reuse an old answer) of **86400 s = 24 h**. It was raised in March 2025 to cut the DNS bill. So a bungee done by DNS can take up to 24 hours to reach everyone, not 15 minutes. Lowering the TTL now doesn't help tonight, because servers keep the 24 h value they already saved.

**My assumption:** the live TTL is still 86400. My only source is a zone export from 30 Oct.

## Live example: at 22:20, k-east's error rate goes over 1%

A user's phone looked up the API at 22:05.

| | Runbook as written | A: switch at old-dc's balancer | B: only prep tonight |
|---|---|---|---|
| Where the phone goes at 22:05 | k-east | old-dc, which passes the request to k-east | old-dc |
| What happens at the bungee | DNS changed back, but the phone keeps using k-east until ~22:05 **tomorrow** | balancer switched back, so old-dc serves the request within seconds | nothing to undo |
| What the user sees | errors for up to a day | a few failed requests for a few minutes | nothing changes tonight |

## Options

**A. Switch at old-dc's balancer tonight**
DNS stays on old-dc. At 22:00, old-dc's balancer starts passing requests to k-east. The bungee is switching it back.
- Pros: the bungee takes seconds for everyone; the announced window still happens; k-east gets real load tonight.
- Cons: the path from old-dc's balancer straight to k-east is **untested**. The traffic copy in OPS-133 went through a separate "mirror agent", and today's balancer config has no k-east entry. It also has to send the right site name over encrypted HTTPS, or k-east turns it away.
- Cons: it's an unreviewed config change on the live balancer, made during the window, and the runbook has to be rewritten.
- Cons: old-dc stays in the path for every request, adding ~34 ms (about 41 + 34 ≈ 75 ms against today's 63). Moving DNS later is still needed before OPS-141.

**B. Only prep tonight; move DNS later**
Tonight: lower the TTL to 300 s, scale k-east up and check it. Then switch DNS at least 24 hours later, and keep the TTL low until OPS-141. The bungee is changing DNS back, which takes about 5 minutes.
- Pros: no improvised changes; the runbook stays almost as it is; k-east serves directly with no extra hop.
- Cons: breaks the announced window, so the status page needs a new date. That eats into the 30 Nov lease along with OPS-141's week without a rollback.
- Cons: the bungee only works if nobody raises the TTL back during that week. Also, some clients hold on to old answers longer than the TTL says.

(Running the runbook as written fails the bungee, so it's not an option.)

## Recommendation

**A, leaning.** It's the only option that keeps tonight's window and still gives a bungee under 15 minutes. The strongest argument against it is the untested balancer-to-k-east path. That doesn't win, because the instant bungee covers that risk. It's also checkable before 22:00: from `lb-1`, send a `/healthz` request to 198.51.100.24 with the right site name. If that check fails, or you won't allow an unreviewed balancer change, take B.

## Questions

1. **A or B?**
2. **What `api` TTL does the live DNS console show right now?** If it was lowered to about 300 s before 22:00 Sunday, the runbook works as written and neither A nor B is needed.
3. **For A: can someone check, before 22:00, that `lb-1` can reach 198.51.100.24 directly over HTTPS?**

---

## Run 2

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts PASS, no-trap-pick PASS, references PASS; 940 words

I need your decision before 22:00 UTC tonight (Mon 2 Nov). I haven't changed any files.

**Context**

- **What we're doing.** OPS-140 is tonight's ticket to move `api.stagelark.example` (the public API) from **old-dc** to **k-east**. old-dc is the leased datacenter: an HAProxy load balancer on `lb-1` at 203.0.113.10 in front of three app VMs. k-east is the new Kubernetes cluster, reachable through its ingress (its public entry point) at 198.51.100.24. The window is 22:00–23:00 UTC and was announced on the status page. Both sites run the same image against the same Postgres database (`pg-main`), so no data moves; only the place that answers requests changes.
- **Already done.** OPS-133 confirmed k-east is ready: 72 hours of copied live traffic, no errors, p95 of 41 ms on k-east vs 63 ms on old-dc. p95 means 95% of requests finish faster than that. The trip from old-dc to k-east takes 34 ms.
- **What comes after.** OPS-141 shuts down old-dc once OPS-140 has run a week without a rollback. The lease ends 30 Nov.
- **Decided by you:** the **bungee**, meaning pointing the API back at old-dc if k-east misbehaves, has to work within **15 minutes**.
- **The problem.** The runbook (`docs/CUTOVER.md`) cuts over by changing the DNS A record (the name→IP entry) from 203.0.113.10 to 198.51.100.24. Its bungee is changing it back. But the TTL on that record is **86400 s (24 h)**. The TTL is how long resolvers (ISP and phone DNS caches) may keep using an answer before asking again. It was raised in March 2025 to cut the DNS bill. So after a bungee, users who already switched can stay on k-east for up to 24 hours. Lowering the TTL now doesn't help tonight, because caches keep the 24 h value they already have.
- **My assumption, not checked:** the live TTL is still 86400. The only copy in the repo is an export from 30 Oct, which I read earlier this session. Re-reading it just now was denied by permissions. If someone lowered it to about 300 s before 22:00 yesterday, the runbook works as written.

**Live example.** At 22:30, k-east's p95 jumps to 400 ms. That breaks the runbook's rollback rule (error rate >1% or p95 >300 ms for 5 minutes). On-call does the bungee at 22:35. Take a user whose phone resolved the API at 22:05:

| | Where that user's app goes after 22:35 | Back on old-dc |
|---|---|---|
| Runbook as written | Still k-east (cached 198.51.100.24) | Up to Tue 22:05: a slow app for a day |
| A: switch at HAProxy | old-dc VMs | Within seconds |
| B: postpone | Never left old-dc | — |

**Options** (if the live TTL is 86400)

**A. Cut over inside HAProxy tonight.** DNS stays on 203.0.113.10. At 22:00, old-dc's HAProxy starts forwarding requests to k-east's ingress. The bungee is switching it back. Lower the API's TTL to 300 s tonight, and move the DNS record at least 24 h later.
- Pros: the bungee takes seconds for everyone; the announced window holds; k-east carries real traffic tonight.
- Cons: a new HAProxy config on the single load balancer for all traffic, not reviewed for this window and written under time pressure. It needs TLS with SNI (sending the hostname during the TLS handshake), a `Host: api.stagelark.example` header (the ingress only matches that hostname), and a health check that sends that header, or k-east gets marked down.
- Cons: this exact path has never carried a real response. The shadow test ran through a separate "mirror agent", not through HAProxy itself (`haproxy.cfg:2`).
- Cons: users get roughly +34 ms per request. My estimate is a p95 around 75 ms vs 63 ms today.
- Cons: k-east sees every request coming from HAProxy's IP, so any per-client logic needs `X-Forwarded-For`.
- Cons: old-dc stays in the path, so OPS-141 can't start until the DNS move happens.

**B. Prep only tonight; cut over by DNS later.** Lower the TTL to 300 s, scale k-east to 6 replicas, and check `/healthz`. Then run the existing runbook at least 24 h later, keeping the TTL low until OPS-141.
- Pros: no unreviewed change to the live load balancer; the runbook stays almost as written; the bungee is about 5 minutes.
- Cons: you break a publicly announced window and need a new one.
- Cons: DNS cutovers drain slowly. Some clients (some JVMs, long-lived connections) ignore the TTL, so the bungee is "about 5 min", not guaranteed.
- Cons: the DNS bill goes up while the TTL is 300 s.

**Recommendation: A, leaning.** It's the only option that both keeps the window and meets the 15-minute bungee. If the new HAProxy config misbehaves, its bungee is a config revert that takes seconds.

The strongest argument against A is that you'd be changing the one load balancer for all traffic, live, with an unreviewed config on a path that has never served real responses. It still wins only if someone can write the backend tonight and review it (`haproxy -c` to validate the config), and test it with the right hostname before 22:00. If nobody can, choose B.

**Questions**

1. What TTL does the DNS console show right now for `api`? If it's ≤300 s and was set before Sun 22:00, we run the original runbook.
2. If it's 86400: **A** (HAProxy tonight) or **B** (postpone)?
3. If A: who writes and reviews the HAProxy backend before 22:00? And is about +34 ms per request acceptable until the DNS move?
4. Lower the `api` TTL to 300 s tonight, whichever option you pick: yes or no?

---

## Run 3

all-decisions FAIL, decision-1 FAIL, decision-2 PASS, facts PASS, no-trap-pick PASS, references FAIL; 842 words

I haven't changed any files. Two decisions are open, and they're both below.

## Context

**What we're doing.** OPS-140 moves the public API, `api.stagelark.example`, from the old data centre ("old-dc") to a Kubernetes cluster ("k-east"). The window is tonight, Mon 2 Nov, 22:00–23:00 UTC, and it was announced on the status page last week. Users shouldn't notice anything: both sites run the same app version (`stagelark-api:2026.10.29`) against the same Postgres database (`pg-main`), so no data moves. Only the machine that answers requests changes. Old-dc's lease ends 30 Nov. OPS-141 shuts old-dc down once k-east has run a week without anyone switching back.

**The places involved:**
- **old-dc today:** a load balancer, HAProxy on `lb-1` at 203.0.113.10. It handles HTTPS and spreads requests over three app servers.
- **k-east:** 198.51.100.24. It has run 2 copies of the app (the runbook raises this to 6) with no live traffic. OPS-133, the readiness test, copied live traffic to it for 72 hours: zero errors, 95% of responses within 41 ms (old-dc: 63 ms). Network round trip between the sites: 34 ms.
- **DNS:** the record that tells users' devices which address to use. `api` points at 203.0.113.10 with a **TTL of 86400 s (24 hours)**. That means a device that looked it up may reuse the answer for a day without asking again. TTLs were raised to a day in March 2025 to cut the DNS bill.

**Decided (by you):** "the bungee" means pointing `api.stagelark.example` back at old-dc if k-east misbehaves, and it **must take effect within 15 minutes**.

**Why this needs deciding now.** The runbook (`docs/CUTOVER.md`) switches the DNS record at 22:00. Its rollback, step 5, switches the record back if k-east's errors exceed 1% or its 95th-percentile response time exceeds 300 ms for 5 minutes. With a 24-hour TTL, that bungee takes up to **24 hours**, not 15 minutes. **The runbook as written can't run tonight.**

**My assumption:** the live TTL is still 86400. The only copy here is an export from 30 Oct. For a DNS bungee to work tonight, the TTL had to be lowered before 22:00 yesterday.

**Facts that matter for option A:** old-dc's HAProxy config (`deploy/old-dc/haproxy.cfg`) has never had k-east as a destination. The OPS-133 copy went through a separate "mirror agent" and the responses were thrown away. So nobody has tested HAProxy sending real requests to k-east and handing the answers back to users. k-east's front door also expects HTTPS for the name `api.stagelark.example`.

## Live example

One user's phone looks up `api` at 22:05. k-east starts failing at 22:20, and you trigger the bungee at 22:25.

| | What happens on the phone after 22:25 |
|---|---|
| Runbook as written | Keeps going to k-east, with errors or timeouts, until as late as **22:05 Tuesday** |
| **A:** switch at HAProxy | Works again within seconds. DNS never changed. |
| **B:** postpone | Nothing changes tonight. On cutover day (TTL 300 s), it works again by about 22:30. |

## Options

**A. Do the switch inside HAProxy tonight.** DNS stays on old-dc. At 22:00, HAProxy starts forwarding requests to k-east. The bungee is HAProxy forwarding to its own three servers again. Also lower the `api` TTL to 300 s tonight so the DNS move can happen safely later.
- Pros: bungee in seconds; keeps the announced window; tonight's TTL drop makes the later DNS move safe.
- Cons: a config change nobody has reviewed, in production, during the window. The HAProxy→k-east path is untested, so if it fails at 21:50 the window becomes B anyway. Every request still passes through old-dc, about 34 ms slower (roughly 75 ms vs 63 ms today), so the real move and OPS-141 are still to come.

**B. Only prepare tonight; cut over later.** Lower the TTL to 300 s, scale k-east and check it. Change DNS at least 24 hours later, and keep the TTL low until OPS-141.
- Pros: no new moving parts; the runbook stays as written apart from the bungee wording; one clean move.
- Cons: misses the announced window, so the status page needs a new date. Less slack before 30 Nov for the week without a rollback that OPS-141 requires. A cheaper TTL could quietly come back and break the bungee.

(Running the runbook as written is ruled out because it breaks the 15-minute limit.)

## Recommendation

**A, leaning.** It's the only option that both meets the 15-minute bungee and keeps tonight's window. The strongest case against it: it depends on the untested HAProxy→k-east path, and it adds an unreviewed change to a live window. That doesn't decide it, because the path can be tested from `lb-1` at 21:50, before any user is affected. If the test fails, you drop to B with nothing lost.

## Questions

1. **A or B?**
2. **What TTL does the live DNS console show for `api`, and when was it last changed?** If it's already 300 s or less and was set before 22:00 yesterday, the original DNS runbook meets the bungee, and that becomes a third option.
