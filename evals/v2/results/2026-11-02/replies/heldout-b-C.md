# heldout-b, cell C

## Run 1

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts PASS, no-trap-pick PASS, references PASS; 1462 words

I tried to re-read the repository before answering, but this session is now in "don't ask" mode and every Read, Grep and Glob call was denied. So the facts below come from my reads of the same five files earlier in this session. The last read was my previous answer, when nothing had changed. I haven't re-checked them this time, and I changed nothing.

## What we're doing and why the decision is needed now

Tonight, from **22:00 to 23:00 UTC on Monday 2 November**, we move the public API (`api.stagelark.example`) from the old data center to the new Kubernetes cluster. The written runbook does the switch by changing a DNS record. You set one hard rule: if the new site misbehaves, we must be able to send everyone back to the old site **within 15 minutes**. You named that way back "the bungee."

The runbook can't meet that rule. The DNS record is set so that resolvers keep their saved answer for **24 hours**. Once we switch, we can't reliably switch everyone back for up to a day. That has to be settled before 22:00, so I need your decision now.

## What every code, number and name means

| Item | Meaning |
|---|---|
| **OPS-140** | Tonight's ticket: move `api.stagelark.example` to k-east |
| **OPS-133** (done) | Prep ticket: k-east is ready, shadow-tested |
| **OPS-141** | Later ticket: shut down old-dc once OPS-140 has run a week without a rollback |
| **old-dc** | The old data center, which serves the API today. Its lease ends **30 Nov** |
| **k-east** | The new Kubernetes cluster we're moving to |
| **203.0.113.10** | old-dc's public IP, on HAProxy on server **lb-1**. The API's DNS record points here today |
| **198.51.100.24** | k-east's public IP (its ingress) |
| **HAProxy** | The load balancer at old-dc. It handles TLS and spreads requests over **app-1/2/3** (`10.0.1.11–13:8080`) |
| **`/healthz`** | The health-check URL the app answers |
| **`pg-main`** | The shared managed Postgres. Both sites use it, so no data moves |
| **`stagelark-api:2026.10.29`** | The app image. Both sites run the same one |
| **TTL 86400** | DNS time-to-live of 86,400 s = **24 h** on the `api` record. Raised in March 2025 to cut the DNS bill |
| **TTL 300** | The value I propose: 5 minutes |
| **2 → 6 replicas** | k-east app copies, scaled up at 21:50 |
| **1% / 300 ms / 5 min** | Rollback trigger: error rate above 1% or p95 latency above 300 ms, lasting 5 minutes |
| **p95 41 ms vs 63 ms** | Shadow-test latency: k-east vs old-dc. 95% of requests finished within that time |
| **72 h** | How long the shadow test copied live traffic to k-east (responses discarded) |
| **34 ms** | Network round trip from old-dc to k-east |
| **`api-stagelark-tls`** | The TLS certificate secret k-east's ingress needs |
| **Bungee** | Your term: pointing the API back at old-dc. It must work within **15 min** |

## Live example: what one resolver does

Take an ISP resolver that looked up `api` at 21:55 and got `203.0.113.10` with a 24 h TTL.

- **Runbook as written (DNS switch at 22:00):** this resolver keeps sending its users to old-dc until about **21:55 Tuesday**. Another resolver that first asks at 22:05 gets k-east. If we bungee at 22:20 by changing the record back, the 22:05 resolver keeps sending its users to k-east until about **22:05 Tuesday**. The bungee takes up to 24 h, against a 15 min limit.
- **Switch at HAProxy instead:** DNS never changes, so every resolver keeps `203.0.113.10`. At 22:00 HAProxy starts forwarding requests to k-east. If we bungee at 22:20, HAProxy forwards to app-1/2/3 again and every user is back on old-dc within **seconds**.

## UX example: what an app user sees

Say k-east starts throwing errors at 22:15 and we decide to bungee at 22:20.

- **DNS route:** a user whose resolver picked up k-east keeps getting failed requests and spinners in the app, possibly until tomorrow evening. Their neighbour on a different ISP is fine. Support gets reports we can't fix by changing anything.
- **HAProxy route:** everyone sees errors for the 5 minutes it takes to hit the trigger plus the minute it takes to switch, then the app works again for all of them.

If nothing goes wrong, users notice nothing on either route: same app, same database.

## Options

**A. Switch at HAProxy tonight, move DNS later (my recommendation)**
- Pros: the bungee takes seconds, for everyone. Keeps the announced window. Tonight's monitoring sees all traffic at once. Lower the TTL to 300 tonight and the DNS move becomes safe in a day or two.
- Cons:
  - It's a HAProxy config change nobody reviewed for this window, plus a rewritten runbook.
  - Every request takes an extra ~34 ms detour through old-dc. The rough estimate is p95 around 75 ms, well under 300 ms.
  - old-dc becomes a single point of failure until the DNS move.
  - Traffic in and out of old-dc roughly doubles.
  - k-east sees HAProxy's IP as the client unless it reads `X-Forwarded-For`. That matters for logs and any per-IP rate limits.

**B. Prep tonight, postpone the switch at least 24 h**
- Pros: no improvised config. Once the TTL is 300, the plain DNS runbook meets the bungee (about 5 minutes). Simplest end state.
- Cons: breaks the window announced on the status page. Uses a day or more of the time left before the 30 Nov lease end. The TTL has to stay low until OPS-141, which costs more on the per-query bill.

**C. Run the runbook as written**
- Pros: no changes, keeps the window.
- Cons: **fails the bungee** (up to 24 h). Step 4 ("old-dc requests fall to zero by 22:30") will look like failure even when nothing is wrong.

**D. DNS runbook tonight, but only if the live TTL was already lowered**
- If someone set `api` to about 300 s in the DNS console before 22:00 Sunday, C actually works. The 30 Oct export says it wasn't, but I can't see the live console.

## What my recommendation rests on, and how sure I am

From my earlier reads (not re-checked this turn):
- `dns/stagelark.example.zone:9`: `api 86400 IN A 203.0.113.10`.
- `deploy/old-dc/haproxy.cfg`: HAProxy on 203.0.113.10 is in front of all API traffic, with one `backend app` we can point elsewhere.
- `deploy/k-east/api.yaml`: the ingress only answers for host `api.stagelark.example` over TLS.

**A correction to what I said earlier:** I claimed k-east "has already carried mirrored traffic" from HAProxy. But `haproxy.cfg:2` says the mirroring went **through the mirror agent**. So the direct path from HAProxy to k-east has **never been tested**.

There are two config details to get right for A:
- HAProxy must connect to k-east over TLS with SNI set to `api.stagelark.example`.
- Its health check (`option httpchk GET /healthz`) sends no Host header, so k-east's ingress would likely answer 404. HAProxy would then mark k-east as down. The check has to send `Host: api.stagelark.example`.

How sure I am:
- That C fails the bungee if the live TTL is still 86400: **about 95%**.
- That A is the right approach: **high**.
- That A runs tonight without surprises: **about 70%**, because of the untested direct path and the two config details. A dry run before 22:00 would raise that a lot: from lb-1, `curl https://api.stagelark.example/healthz --resolve api.stagelark.example:443:198.51.100.24`.

## Open questions

1. **A, B, or something else?**
2. In the live DNS console, what's the TTL on `api`? If it's already about 300 and was set before 22:00 Sunday, D works.
3. What time is it for you now? How long until 22:00?
4. Who can change HAProxy on lb-1 tonight, and does your change policy allow an unreviewed config change inside the window?
5. Can lb-1 reach `198.51.100.24:443` directly, not via the mirror agent? Can someone run the curl above before 22:00?
6. Does the 15-minute bungee also apply after the later DNS move, until OPS-141? If so, the TTL stays at 300 until old-dc is shut down.
7. Is it OK to lower the `api` TTL to 300 tonight, given it was raised to cut the DNS bill?
8. Does k-east rely on client IPs (rate limits, logs, geo)? That decides whether A needs `X-Forwarded-For` handling.
9. If B: who updates the status page and picks the new window?
10. Can you restore my read access so I can re-check the files myself? And do you want me to draft the runbook changes? That would mean editing files, which you've told me not to do so far.

I'll stop here until you answer.

---

## Run 2

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 1102 words

I couldn't re-check the project just now. The file reads were denied in this mode. Everything below comes from my reads earlier in this session, the last one shortly before your message. I haven't changed any files.

## What we're doing and why it needs deciding now

Tonight (Mon 2 Nov, 22:00–23:00 UTC) the team moves the public API, `api.stagelark.example`, from the old data centre to the new Kubernetes cluster. Your rule is that the way back has to work within 15 minutes. The written runbook does the move by editing DNS, and that can't meet the rule. So before 22:00 someone has to choose how tonight runs.

## What the names and numbers mean

- **OPS-140**: tonight's ticket, moving the API to k-east. Runbook: `docs/CUTOVER.md`.
- **OPS-133**: done. It shows k-east is ready: same image, a 72-hour shadow test with no errors.
- **OPS-141**: shutting down old-dc. It's allowed only after OPS-140 has run a week with no rollback, and the old-dc lease ends 30 Nov.
- **old-dc**: the current site. HAProxy (a load balancer) on `lb-1` at **203.0.113.10** sends requests to three app machines, `10.0.1.11–13`.
- **k-east**: the new cluster, reached at **198.51.100.24**. It runs 2 copies of the API today, and the runbook raises that to 6.
- **pg-main**: the database both sites share, so no data moves.
- **TTL 86400**: DNS answers for `api` may be stored by resolvers for 86400 seconds (24 hours). It was raised to a day in March 2025 to cut DNS costs (`dns/stagelark.example.zone:2,9`).
- **34 ms**: the network round trip from old-dc to k-east.
- **41 ms / 63 ms**: p95 response time (95% of requests are faster) on k-east and on old-dc.
- **1% / 300 ms for 5 min**: the runbook's rollback trigger.
- **The bungee**: your name for the way back, pointing `api.stagelark.example` at old-dc again. It must work within 15 minutes.

## Live example

The runbook changes DNS at 22:00. A user's phone looks up `api` at 22:05 and gets 198.51.100.24 (k-east), which it may keep for 24 hours. At 22:20 k-east starts failing, and at 22:25 the team does the bungee by changing DNS back. That phone keeps calling k-east until about 22:05 Tuesday. The bungee takes up to a day, not 15 minutes.

The same thing happens on the way in. Resolvers that stored 203.0.113.10 before 22:00 keep sending people to old-dc for up to a day. Step 4's "old-dc should fall to zero by 22:30" won't happen.

## What users would see

Say k-east breaks at 22:20.
- **DNS runbook:** some users get errors or a broken app from 22:20 until sometime Tuesday, depending on when their resolver last looked the record up. Support can't fix it for them.
- **HAProxy cutover (option A below):** every user goes through old-dc's HAProxy. Switching its backend back to the old machines brings everyone back within seconds, so users see a few minutes of errors at most.
- **Speed under A:** each request takes the extra hop from old-dc to k-east. A rough estimate is a p95 of about 41 + 34 ≈ 75 ms against 63 ms today. That's a little slower, and most people won't notice.

## Options

**A. Cut over at HAProxy tonight, move DNS later (my recommendation)**
At 22:00, point HAProxy's backend at k-east and keep the three old machines in the config for the bungee. Lower the `api` TTL to 300 seconds tonight, and move DNS at least 24 hours later.
- Pros:
  - Keeps the announced window.
  - The bungee takes seconds.
  - All traffic moves at once, so the 22:00–22:30 watch actually measures k-east.
- Cons:
  - It's a HAProxy config change nobody has reviewed, made during a deploy freeze.
  - HAProxy has never sent traffic to k-east as a backend. This is a contradiction in the project files: `haproxy.cfg:2` says the shadow test went "through the mirror agent", while `TICKETS.md` says HAProxy mirrored it. The new path needs TLS to 198.51.100.24 with the hostname `api.stagelark.example` (the Ingress only matches that host) and a health check.
  - Adds about 34 ms per request.
  - old-dc stays in the path, so an outage there still takes the API down.
  - k-east sees HAProxy's address instead of the client's.
  - It's two cutovers instead of one, and OPS-141's week can't start until DNS also moves.

**B. Prep only tonight, cut over by DNS in at least 24 hours**
Lower the TTL to 300 and scale and check k-east tonight. Run the runbook as written in a new window, and keep the TTL low until OPS-141.
- Pros:
  - No new config. The runbook barely changes.
  - Users go straight to k-east, with no extra hop.
  - The bungee is about 5 minutes.
- Cons:
  - Misses the announced window, so the status page needs a new one.
  - DNS costs more per query while the TTL is low.
  - Leaves less slack before the 30 Nov lease end, though still plenty.

**C. Run the runbook as written tonight**
- Pros: nothing changes.
- Cons: the bungee takes up to 24 hours, which breaks your rule. This is only acceptable if the live TTL was already about 300 seconds since before Sunday 22:00.

## Recommendation and how sure I am

I recommend **A, provided someone confirms before 22:00 that `lb-1` can reach k-east**, for example from lb-1: `curl --resolve api.stagelark.example:443:198.51.100.24 https://api.stagelark.example/healthz`. If that can't be shown working in time, choose **B**.

- **Fairly sure (about 90%) that the written runbook fails the bungee.** The one doubt: the zone file is an export from 30 Oct, and the live TTL might have changed since.
- **Less sure (about 65%) that A can be done safely tonight.** The HAProxy-to-k-east path has never been tested, and the change hasn't been reviewed.

## Open questions

1. What does the DNS provider's live console show as the `api` TTL right now, and when did it last change?
2. A, B or C?
3. If A: who can change HAProxy on `lb-1`, and is that allowed during the deploy freeze? Can someone run the lb-1 → 198.51.100.24 test before 22:00?
4. Can the `api` TTL be lowered to 300 tonight, given that it was set to a day to save money?
5. Does the API rely on the client's IP for anything, such as rate limits, geo rules or audit logs? That matters for A.
6. If B: who updates the status page, and what's the new date?
7. Do you want to allow file reads again so I can re-check the project before you decide?

I'll wait for your answers.

---

## Run 3

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts PASS, no-trap-pick PASS, references PASS; 1282 words

I tried to re-read the five project files before writing this, but this turn those reads were **denied** ("don't ask" permission mode). So I could not re-check anything just now. Every fact below comes from my reads earlier in this session. The last of those was a few minutes before your last message, and the files hadn't changed between reads. I changed nothing.

## What we're doing and why it needs a decision now

Ticket **OPS-140** moves the public API, `api.stagelark.example`, from the old data centre (**old-dc**) to the new cluster (**k-east**). The window is **tonight, Mon 2 Nov, 22:00–23:00 UTC**, and it was announced on the status page last week. You set one hard rule: **the bungee** (pointing the API back at old-dc if k-east misbehaves) **must work within 15 minutes**.

The written runbook (`docs/CUTOVER.md`) switches by changing DNS, and the DNS record is cached for **24 hours**. So its bungee can take up to a day, not 15 minutes. The runbook can't run as written, and someone has to choose a different plan before 22:00.

## What every code, number and name means

| Item | Meaning |
|---|---|
| **OPS-140** | Tonight's move of the API from old-dc to k-east |
| **OPS-133** | Done: proved k-east is ready (same image, 72 h shadow test, no errors) |
| **OPS-141** | Later: shut down old-dc and release its IP, after OPS-140 runs a week without a rollback. The old-dc lease ends **30 Nov** |
| **old-dc** | The current site: HAProxy load balancer on host `lb-1` in front of 3 app VMs (`app-1..3`, `10.0.1.11–13:8080`) |
| **k-east** | The new Kubernetes site. Deployment `stagelark-api`, 2 replicas today, 6 planned for tonight |
| **203.0.113.10** | old-dc's HAProxy, the public IP the API uses today |
| **198.51.100.24** | k-east's ingress (its public entry point) |
| **A record** | DNS entry mapping `api.stagelark.example` to an IP. Today it's 203.0.113.10 |
| **TTL 86400** | How long resolvers may cache that answer: 86400 s = 24 h. Raised in March 2025 to cut the DNS bill |
| **300 (TTL)** | 5 minutes, the value I'd lower it to |
| **pg-main** | The managed Postgres both sites share, so no data moves |
| **`stagelark-api:2026.10.29`** | The app image, the same on both sites |
| **`/healthz`** | Health-check URL |
| **1% / 300 ms / 5 min** | Runbook rollback trigger: k-east error rate above 1% or p95 latency above 300 ms, sustained for 5 minutes |
| **p95 41 ms vs 63 ms** | Shadow-test latency: k-east 41 ms, old-dc 63 ms |
| **34 ms** | Round trip from old-dc to k-east |
| **The bungee** | Your name for pointing the API back at old-dc; must work in ≤15 min |

## A live example

A user's DNS resolver looks up `api` at **22:10**, after the DNS switch, gets k-east, and caches it for 24 h. At **22:20** k-east's error rate reaches 5%. At **22:25** the trigger fires and we:

- **DNS bungee (runbook as written):** set the record back to old-dc. That user's resolver keeps k-east until **22:10 Tuesday**, so they're stuck on the broken site for about a day. ❌
- **HAProxy bungee (option A):** DNS never changed, so everyone still reaches 203.0.113.10. We flip HAProxy's backend from k-east back to the app VMs, and within seconds every request goes to old-dc. ✅

## The same thing from a user's side

- **DNS bungee:** some users get errors or slow pages for up to a day after we "rolled back." The status page says resolved, support tickets keep coming in, and we can't fix it from our end.
- **HAProxy cutover:** users notice nothing at 22:00. Latency rises by about 34 ms (k-east's 41 ms plus 34 ms is about 75 ms p95, compared with 63 ms today). In a bungee, requests in flight at that moment may fail once, and the next one works.
- **Postpone:** users notice nothing tonight. The status page shows the window as rescheduled.

## Options

**A. Cut over at old-dc's HAProxy tonight; move DNS later (my recommendation)**
- ✅ The bungee takes seconds, well inside 15 min, whatever the DNS TTL.
- ✅ Keeps tonight's announced window. Rollback doesn't depend on any client's cache.
- ✅ Lower the `api` TTL to 300 tonight too. Then a DNS change about 24 h later has a ~5-min bungee of its own.
- ❌ An unreviewed HAProxy change inside the window, and the runbook has to be rewritten on the spot.
- ❌ **Not proven:** HAProxy sending live traffic straight to k-east. The OPS-133 shadow test went "through the mirror agent" (`haproxy.cfg:2`), not through HAProxy server lines. So TLS to the ingress with SNI `api.stagelark.example`, and reachability from `lb-1` to `198.51.100.24:443`, are untested. Earlier I said k-east had "already carried mirrored traffic" through this path, and that overstated it.
- ❌ k-east sees `lb-1`'s IP as the client. That needs `option forwardfor` if the app uses client IPs.
- ❌ old-dc stays in the request path, not just the way back, until the DNS move. That move has to happen well before 30 Nov.

**B. Prep only tonight, cut over by DNS at least 24 h later**
- ✅ The simplest mechanism, and the runbook barely changes.
- ✅ With TTL 300, the bungee is about 5 min plus detection time.
- ❌ Misses the announced window, so the status page needs a reschedule.
- ❌ The TTL has to stay low until OPS-141. That raises the DNS bill, and if anyone raises the TTL again, the bungee breaks.
- ❌ Some clients cache longer than the TTL says (some JVMs, long-lived connections), so a few stragglers are possible.

**C. Run the runbook as written**
- ✅ No changes.
- ❌ Fails the bungee: up to 24 h instead of 15 min. Only acceptable if the live TTL was already lowered before **22:00 Sunday**.

## Check and confidence

- The fact my recommendation rests on is `api 86400 IN A 203.0.113.10` (`dns/stagelark.example.zone:9`). I confirmed it in earlier reads, but I **couldn't re-check it this turn**. It also comes from a **30 Oct export**, so it may not match the live DNS console.
- **High confidence:** with a 24 h TTL, the runbook fails the bungee.
- **Medium confidence:** the live TTL is still 86400.
- **Medium-high confidence:** option A works. The idea is sound, but the HAProxy→k-east path (TLS/SNI, reachability, the `api-stagelark-tls` certificate in k-east) has never carried live traffic. It should be tested at 21:50 before committing.

## My questions, all at once

1. Which plan: **A**, **B**, or **C**?
2. What TTL does the **live DNS console** show for `api` right now?
3. Does the 15 minutes count **from when the problem starts**, so it includes the 5-minute detection window, or **from when we decide to bungee**?
4. For A: who can edit and reload HAProxy on `lb-1` tonight, and does your change policy allow an unreviewed config change inside the window?
5. For A: can the on-call engineer test `lb-1` → `198.51.100.24:443` with SNI `api.stagelark.example` at 21:50, and treat a failure as an automatic switch to B?
6. Does the app depend on client IPs (rate limits, geo, audit logs)? That decides whether `forwardfor` is required.
7. OK to lower the `api` TTL to 300 tonight and keep it there until OPS-141, accepting the higher DNS bill?
8. For B: who updates the status page, and what's the new date?
9. Do you want to re-allow file reads so I can re-verify the files before you decide?

I'll wait for your answers before doing anything else.
