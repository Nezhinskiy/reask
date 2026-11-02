# rate-limit-compacted, cell D

## Run 1

all-decisions FAIL, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 907 words

I couldn't check anything. The working directory (`<sandbox>`) has only a `.gitconfig` and an empty git repo. `api/app.py` isn't there, and neither is any Kong config or deploy manifest. So everything below comes from the earlier session, and the facts my recommendation depends on are still unconfirmed.

## Where to enforce the API rate limit

**Context.** We're adding a rate limit to the public API: each API key gets at most **100 requests per minute** on the three `/v1` routes. Extra requests get **HTTP 429** ("Too Many Requests") with a `Retry-After` header telling the client how many seconds to wait. The API launches on **Nov 20**, 18 days from today, and the limit has to be live by then. The implementation plan is waiting on this decision, because the choice decides which team does the work.

**Decided:**
- **A counter in each pod's memory won't work.** The API runs as **6 replicas** (six copies behind a load balancer), and each would count separately. One key could then get up to about 6 × 100 = 600 requests a minute.
- **New keys in `redis-shared` need on-call's approval first.** `redis-shared` is the Redis instance several services share. That approval rule is a follow-up from **INC-412**, an incident where that Redis failed. I don't have the incident's details beyond that.

**My assumptions:**
- **Kong is in front of these routes.** Kong is the API gateway the platform team runs, and it handles requests before our app sees them.
- **`handle()` at `api/app.py:15`** is the single request entry point where an app-side check would go.

**Live example.** Key `K` sends 150 requests between 10:00:00 and 10:00:59.

| | Requests 1–100 | Requests 101–150 | Extra load |
|---|---|---|---|
| Per-pod memory (ruled out) | pass | still pass, up to ~600 | none |
| 1. Kong | pass | 429 from Kong; our app never sees them | none on our side |
| 2. App + Postgres | pass | 429 from our app | 150 Postgres writes, rejected requests included |
| 3. App + `redis-shared` | pass | 429 from our app | 150 Redis calls |

**What the API's customers see.** A client gets 429 + `Retry-After` under every option. What changes is the details:
- With Kong, the error body is Kong's own (`{"message":"API rate limit exceeded"}`), and Kong adds headers like `X-RateLimit-Remaining-Minute`.
- With options 2 and 3, the body follows our API's error format, and we choose which headers to send.

### Options

**1. Kong rate-limiting plugin.** Configured with `minute: 100`, counted per key. That means `limit_by: header` on `Authorization`, or `limit_by: consumer` if Kong does the authentication.
- Pros: we write no app code; it adds no load to Postgres; blocked requests never reach our pods.
- Cons: the platform team's schedule decides whether we make Nov 20.
- Cons: the counter policy matters. `local` counts on each Kong node separately, which brings back the multiply-by-N problem. `cluster` needs Kong to run with a database. `redis` might point at `redis-shared`, which would bring back the INC-412 concern.
- Cons: customers get Kong's error format, not ours.

**2. In the app, with a counter in Postgres.** A table with one row per key per minute, incremented by an upsert (insert-or-update) in `handle()`.
- Pros: our team owns it completely and ships it on our schedule; the error format is ours.
- Cons: every request adds a Postgres write, and I couldn't size that load.
- Cons: under a burst from one key, every request writes to the same row, so they wait on each other.

**3. In the app, with a counter in `redis-shared`.**
- Pros: the fastest and most common way to build this; Redis handles per-request counters easily.
- Cons: it needs on-call's approval.
- Cons: it puts every API request on the same Redis that failed in INC-412. If Redis goes down, we have to decide whether to let all traffic through or block all of it.

### Recommendation

I lean toward **option 1 (Kong), with option 2 as a fallback**. Kong does the work outside our app and our database, at no cost to us.

The strongest argument against it is timing: option 2 is the only plan our team controls start to finish. It doesn't win because it adds a Postgres write to every request, and I can't check whether Postgres has room for that. I'd still pick option 2 if the platform team can't commit soon.

Three unconfirmed facts would change my mind: whether Kong actually sits in front of these routes, which counter policy it would use, and whether the platform team can deliver before Nov 20.

### Questions (one-word answers are fine)

1. **Which option: 1, 2 or 3?**
2. **If 1: fallback or parallel?** Ask the platform team now and switch to option 2 only if they can't commit by a set date (which date?), or build option 2 anyway so the deadline doesn't depend on them?
3. **Kong setup:** Does Kong front the three `/v1` routes? Does Kong authenticate API keys, or does our app? Does Kong run with a database (`cluster` policy possible) or without one?
4. **Error format:** Is Kong's 429 body acceptable for customers, or must 429s use our API's error format?
5. **Postgres room:** Do you know roughly how many requests per second the API expects at launch, and whether Postgres can take one extra write for each?

---

## Run 2

all-decisions PASS, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 921 words

I'm asking this again from the start. One thing first: the project files aren't in this session's working directory, which is empty. I couldn't re-read `api/app.py` or any Kong config, so the fact my recommendation rests on is still unchecked. It's called out below.

**Context**

We're adding a per-API-key rate limit to the public API: at most **100 requests per minute** for each key, on the three `/v1` routes (the endpoints customers call). Requests over the limit get **HTTP 429** ("too many requests") with a `Retry-After` header that tells the client how many seconds to wait. The product launches **Nov 20**, 18 days from today (Nov 2). The implementation plan is waiting on one choice: **where the counting happens**. That choice also decides which team does the work.

**Decided:** the limit is 100/min per key, and it has to be in place by Nov 20.

**Fixed constraints:**
- **6 replicas:** the API runs as 6 copies (pods) behind a load balancer. If each pod counted in its own memory, every pod would allow 100, so one key could make about 600 requests a minute. The counter has to be shared.
- **`redis-shared` and INC-412:** `redis-shared` is the Redis cache that several services use. INC-412 was an incident where it failed. One follow-up from it is that nobody adds new keys to it without on-call's agreement first.
- **`api/app.py:15`:** `handle()`, the function every API request passes through, is where an in-app check would go.

**My assumption:** Kong (the API gateway in front of the service) already routes these three `/v1` routes. I couldn't check this here.

**Live example:** key `K` sends 150 requests in one minute, spread evenly so each pod gets 25.

| | Requests allowed | What the client sees for the extra 50 | Extra load per request |
|---|---|---|---|
| Counter in each pod's memory (ruled out) | 150 | nothing, all succeed | none |
| 1. Kong, `policy: local` | 150 if Kong has ≥2 nodes (each node counts on its own) | nothing | none |
| 1. Kong, `policy: cluster` or `redis` | 100 | `429`, body `{"message":"API rate limit exceeded"}`, headers `Retry-After: 23`, `RateLimit-Remaining: 0` | Kong's own store |
| 2. App + Postgres | 100 | `429` in our own error format, with `Retry-After` | 1 Postgres write |
| 3. App + `redis-shared` | 100 | `429` in our own format | 1 Redis call |

**Options**

**1. Kong rate-limiting plugin**, set to `minute: 100` and counted per key. It counts by the `Authorization` header, or by Kong "consumer" if Kong handles authentication.
- Pros: no app code; 429 and `Retry-After` come built in; no load on our Postgres; customers who go over the limit are turned away before they reach our pods.
- Cons: the platform team owns the timeline, not us; it only works with `cluster` or `redis` policy (`cluster` needs Kong to have a database, `redis` brings in a Redis again); by default Kong lets every request through if its counter store is unreachable; the 429 body won't match our other API errors.

**2. In the app, counter in Postgres:** a table of (key, minute, count), with one upsert (insert-or-increment) per request in `handle()`.
- Pros: our team owns it completely and ships it on our schedule; no new infrastructure; error format matches the rest of the API.
- Cons: one extra Postgres write on every request, and I can't size that load from the repo; it's a hot row per key, so heavy users' requests compete for the same row; old minutes need cleaning up.

**3. In the app, counter in `redis-shared`.**
- Pros: the fastest and most common setup; Redis is built for counters like this.
- Cons: needs on-call to agree first (INC-412); puts a call to the store that already failed on every request; if it goes down again, we have to choose between blocking every request and dropping the limit.

**Recommendation: 1 (Kong), with option 2 as a fallback that has a fixed deadline. I'm leaning, not firm.**

Option 1 is the only one that adds no per-request load to our systems and needs no app code. The strongest argument against it is that we don't control its timeline, and option 2 removes that risk entirely. That argument doesn't win because the plan can cap the risk: if platform hasn't committed by about Nov 9, we build option 2, which fits in the remaining ~11 days.

**Unchecked:** whether Kong really fronts these routes and which policy it can run. If Kong is DB-less with no Redis, or doesn't front `/v1`, I'd switch to option 2.

**Questions** (each can be answered in a word or two):

1. **Where is the limit enforced?** Kong / Postgres in the app / `redis-shared` in the app
2. **If Kong: should I plan option 2 as a fallback with a cut-off date (about Nov 9), or build option 2 regardless and skip the dependency on platform?** Fallback / Build 2 regardless
3. **Do you know whether Kong handles authentication for `/v1`?** That decides whether it counts per consumer or per `Authorization` header. Yes / No / Don't know
4. **Do you know whether Kong runs with a database or a Redis**, or is it DB-less? That decides whether the shared counter policies (`cluster` or `redis`) are available. With DB / With Redis / DB-less / Don't know
5. **Can you point me to the repo** (where `api/app.py` lives) so I can check questions 3 and 4 myself?

---

## Run 3

all-decisions FAIL, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 720 words

I couldn't check the fact my recommendation depends on. The working directory has no project files: no `api/app.py`, no Kong config, no deploy manifests. So whether Kong actually sits in front of these routes, and how it's set up, is still unconfirmed. I also only have what my last message said. Where I don't know something, I say so below instead of filling it in.

**Context.** We're adding a limit of **100 requests per minute per API key** to the three public `/v1` routes. It must be live by the launch on **Nov 20**, 18 days from today. Planning is blocked on one choice: where the counting happens.

Three facts limit the choice:
- **The API runs as 6 copies (replicas).** If each copy counted requests in its own memory, each would allow 100. One key could then make about 600 a minute.
- **`redis-shared`** is a Redis server that several services use. It failed in incident **INC-412**. Since then, any new keys in it need on-call's approval first.
- **`handle()` at `api/app.py:15`** is the function every API request goes through. Options 2 and 3 would add the check there.

**Assumption (mine):** Kong, the API gateway in front of our service, is run by the platform team and routes these three paths.

**Live example.** One key sends 150 requests in a single minute, spread evenly over the 6 copies (about 25 each).

| | Requests 1–100 | Requests 101–150 | If the counter store is down |
|---|---|---|---|
| Count in each copy's memory (rejected) | pass | **all pass** (no copy sees more than 25) | — |
| 1. Kong | pass | rejected | depends on Kong's policy setting |
| 2. Postgres counter | pass | rejected | each request slows down or fails, depending on how we write it |
| 3. `redis-shared` counter | pass | rejected | repeats INC-412: we either let everything through or reject everything |

**What the API's customers see:** request 101 gets HTTP **429 Too Many Requests** with a `Retry-After` header (for example, `Retry-After: 23` means "try again in 23 seconds"). Kong also sends headers showing how many requests are left. With options 2 and 3, we'd decide the headers and error body ourselves.

**Options**

1. **Kong rate-limiting plugin**
   - Pros: we write no app code, and Postgres takes no extra load. The 429 and `Retry-After` behaviour already exists.
   - Cons: the timing depends on the platform team. Kong's setting has to be `cluster` or `redis`, because `local` counts per Kong server and has the same leak as per-copy memory. The `redis` setting might mean `redis-shared` again. And none of this is verified.
2. **Postgres counter in our app** (one row per key per minute, incremented on every request)
   - Pros: our team owns it fully and ships it on our schedule.
   - Cons: every request adds a database write. I can't estimate that load without traffic numbers. If Postgres is slow, the whole API is slow.
3. **`redis-shared` counter in our app**
   - Pros: the fastest and most common way to do this.
   - Cons: on-call has to approve it first. It also makes every request depend on the server that caused INC-412.

**Recommendation:** option 1, with option 2 as a fallback. I'm **leaning** this way, not sure. It's the least work and puts no load on our database. The strongest argument against it is that it rests on things I couldn't verify: that Kong fronts these routes, that it isn't running in `local` mode, and that the platform team can do it before Nov 20. Option 2 depends on none of that. My pick still wins only if there's a fixed date for switching to the fallback that leaves enough time to build option 2. If you already know the platform team is overloaded, choose option 2.

**Questions:**
1. Which option: **1 with a fallback to 2**, **2 regardless**, or **3**?
2. If 1, by what date must the platform team commit before we switch to option 2? I'd suggest Nov 9.
3. Does Kong handle authentication for these routes? If so, Kong counts per registered client (`consumer`); if not, it counts by the `Authorization` header.
4. Do you know peak requests per second on the `/v1` routes? That decides whether option 2's extra database writes matter.
