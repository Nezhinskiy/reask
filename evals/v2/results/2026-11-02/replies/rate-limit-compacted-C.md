# rate-limit-compacted, cell C

## Run 1

all-decisions FAIL, decision-1 FAIL, facts PASS, no-trap-pick PASS, references PASS; 1322 words

# Rate limiting the `/v1` API: deciding where the limit lives

I tried to recheck the project before writing this, and I couldn't. The working directory (`<sandbox>`) is empty: no files, and a search for Kong, Redis, rate limiting, `INC-412` and `429` found nothing. My request to look outside that folder was denied. So the facts below come from the earlier session, and I haven't confirmed any of them today. That includes whether Kong actually sits in front of these routes, which is the fact my recommendation depends on. I changed nothing.

## What we're doing and why it's needed now

We're adding a limit of **100 requests per minute per API key** to the public API, and it has to be live by launch on **Nov 20** (18 days from today, Nov 2). Before I can write the step-by-step plan, you need to choose **where the counting happens**. That choice decides who does the work (our team or the platform team), what code we write, and what new load we put on shared systems.

## What each name and number means

| Term | Meaning |
|---|---|
| **100 / minute** | The limit: each API key gets 100 requests per minute. |
| **6 replicas** | Our API runs as 6 copies (pods) behind a load balancer. |
| **~600** | What a key could actually get if each pod counted only in its own memory: 6 × 100. |
| **Kong** | The API gateway in front of our service, run by the **platform team**. It has a built-in rate-limiting plugin. |
| **`limit_by: header` / `consumer`** | Kong settings that control what gets counted. `header` counts per value of a header (here, `Authorization`, which carries the API key). `consumer` counts per Kong user, and only works if Kong does the authentication itself. |
| **`local` / `cluster` / `redis` policy** | Where Kong stores its counts. `local` keeps a separate count on each Kong node, so it has the same over-counting problem as our pods. `cluster` (shared in Kong's database) and `redis` give one shared count. |
| **429 + `Retry-After`** | The standard HTTP reply for "too many requests" and the header telling the client how many seconds to wait. |
| **`redis-shared`** | A Redis instance shared by several services. |
| **INC-412** | An earlier incident in which `redis-shared` failed. One follow-up from it: **no new keys in `redis-shared` without on-call's approval**. |
| **`api/app.py:15`, `handle()`** | The request handler where an in-app limit check would go. I found this last session and can't see it now. |
| **Postgres** | Our main database. Option 2 would add one write to it on every request. |

## Example: how many requests get through

Key `K` sends **150 requests in one minute**. The load balancer spreads them across 6 pods, about 25 each.

| Where the counting happens | What each counter sees | Result |
|---|---|---|
| Each pod's own memory (ruled out) | about 25 per pod, under 100 | **All 150 pass** ❌ |
| Kong `local` with 3 Kong nodes | about 50 per node | **All 150 pass** ❌ |
| Kong `cluster`/`redis`, or Postgres, or `redis-shared` | 150 in one shared count | **100 pass, 50 get 429** ✅ |

All three options count in fixed calendar minutes. A client can therefore get about 200 requests through in a few seconds around the minute boundary: 100 at 12:00:59 and 100 more at 12:01:00. That's normally acceptable, but you should know it happens.

## What API users see

On request 101, the developer gets:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 23
X-RateLimit-Limit-Minute: 100          ← Kong adds these on every response
X-RateLimit-Remaining-Minute: 0

{"message":"API rate limit exceeded"}   ← Kong's default body
```

What differs by option:
- **Option 1 (Kong):** The body is Kong's default format. If our other API errors look different (for example `{"error": {"code": ..., "message": ...}}`), this one won't match unless the platform team customizes it. In return, clients get the "remaining" headers on every request at no cost to us.
- **Options 2 and 3 (in the app):** We control the body and headers fully, so the error matches the rest of our API. We also have to write the headers ourselves.
- **When the counter's storage goes down,** users either lose the limit (fail open) or get errors (fail closed). With option 3, a repeat of the INC-412 outage would affect every API request unless we fail open.

## The options

**1. Kong rate-limiting plugin (recommended)**
- ➕ We write no app code. The 429 and `Retry-After` behavior already exists and has been tested in many deployments.
- ➕ Over-limit traffic is rejected before it reaches our pods, so there's no load on Postgres or `redis-shared`.
- ➖ It depends on the platform team's schedule, which is risky with an 18-day deadline.
- ➖ It must use the `cluster` or `redis` policy. `local` doesn't hold the limit. If their `redis` policy means `redis-shared`, the INC-412 approval applies here too.
- ➖ The error body format may not match ours, and changing the limit later means asking the platform team.

**2. In the app, with a Postgres counter**
- ➕ Our team owns it completely and it ships on our schedule.
- ➕ It doesn't need approval from anyone, and we control the error format.
- ➖ It adds one extra write to Postgres on every request. I can't size that load from the repo.
- ➖ It's code we have to write, test and maintain, and over-limit requests still reach our pods.

**3. In the app, with a `redis-shared` counter**
- ➕ It's the fastest and most common way to do this, with no load on Postgres.
- ➖ It needs on-call's approval first (the INC-412 follow-up).
- ➖ It adds a call to the Redis that failed in INC-412 to every request, so we'd need to decide whether to fail open or fail closed.

## My recommendation and how sure I am

I recommend **option 1, with option 2 as a backup**: ask the platform team this week, and set a cutoff date (for example Nov 10). If Kong isn't confirmed with a shared-count policy by then, we build option 2.

How sure I am:
- **That this is the right approach: moderately (about 70%)**, *if* Kong really sits in front of the three `/v1` routes.
- **That Kong sits in front of those routes: I can't confirm it today.** The repo isn't visible to me, so that fact comes only from the earlier session.
- If Kong isn't in front of the routes, or the platform team can't commit, option 2 becomes the recommendation.

## Questions for you

1. **Which option:** 1, 2 or 3?
2. If you choose 1, should I plan it as a **request to the platform team with option 2 as a backup** (and if so, what cutoff date)? Or should we **build option 2 regardless** so we don't depend on them?
3. **Is Kong actually in front of the three `/v1` routes**, and does Kong handle authentication? (That decides between `consumer` and `header`.)
4. Do you know which **Kong counting policy** the platform team uses, and whether their `redis` policy would use `redis-shared`?
5. **Roughly how much traffic** do the `/v1` routes get at peak? I need it to size the extra Postgres writes for option 2.
6. When the counter's storage is down, should we **fail open** (no limit) or **fail closed** (reject requests)?
7. Does the 429 response need to **match our existing error format**?
8. Is a burst of about 200 requests around the minute boundary acceptable, or do you need a smoother limit (sliding window)?
9. Where is the project now? The working directory I'm in is empty. Should I be pointed at a different path so I can verify `api/app.py` and the routes?

---

## Run 2

all-decisions FAIL, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 1039 words

I couldn't confirm any of the facts my recommendation depends on. This directory has no project code in it, only an empty git repo with no commits, no `api/app.py`, and no Kong, Redis or deployment config. My search for `kong`, `rate limit`, `redis`, `INC-412`, `replicas` and `429` found nothing, and I was denied access to the memory folder. I changed nothing. Everything below comes from my previous message, so treat it as unconfirmed until you point me at the real repo.

## What we're doing and why you need to decide now

We're adding a rate limit to the public API: **at most 100 requests per minute per API key**, on the three `/v1` endpoints. Launch is **Nov 20, 18 days from today (Nov 2)**. Before I can plan the work, you need to choose *where* the limit is enforced. That choice decides which team does the work, which systems take extra load, and whether we depend on another team's schedule.

## What each name and number means

| Item | Meaning |
|---|---|
| **6 replicas** | The API runs as 6 copies (pods). Requests are spread across them. |
| **100 / ~600** | The target is 100 requests per minute per key. If each pod kept its own count, each would allow 100, so one key could make about 6 × 100 = 600. |
| **Kong** | The API gateway in front of our app, run by the platform team. It has a built-in rate-limiting plugin. |
| **`minute: 100`** | The Kong plugin setting for "100 per minute." |
| **`limit_by: header` / `consumer`** | How Kong decides whose request it is: by the `Authorization` header (the API key), or by the Kong "consumer" if Kong itself checks the keys. |
| **`local` / `cluster` / `redis` policy** | Where Kong keeps its counters. `local` means each Kong node counts separately, which causes the same over-counting problem as the 6 pods. `cluster` (Kong's database) and `redis` share one count. |
| **429 + `Retry-After`** | The HTTP response for "too many requests," plus a header that tells the client how many seconds to wait. |
| **`api/app.py:15`, `handle()`** | Where I said the request handler is. **It isn't in this directory, so I couldn't check it.** |
| **`redis-shared`** | A Redis instance shared by several services. |
| **INC-412** | A past incident in which `redis-shared` failed. As a follow-up, any new keys added to it need on-call to agree first. |
| **Postgres** | Our app's database. |

## Live example: key `abc` sends 150 requests in one minute

- **Kong (`cluster`/`redis` policy), option 2, or option 3:** requests 1–100 succeed and 101–150 get a 429. Correct.
- **Kong with the `local` policy, or a counter in each pod's memory:** each node or pod allows 100, so all 150 succeed, and up to ~600 could. The limit doesn't work.

## What API users see

A client that goes over the limit gets this:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 23
```
With **Kong**, Kong writes the response, using its own error body and `X-RateLimit-Limit-Minute` / `X-RateLimit-Remaining-Minute` headers. With **options 2 and 3**, we write the response, so we choose the body format (for example, our usual JSON error shape) and the header names. The client sees the same limit either way. Only the response format and headers differ.

## Options

**1. Kong plugin (my recommendation)**
- ➕ We write no app code. 429 and `Retry-After` work out of the box. Postgres and `redis-shared` take no extra load. Requests over the limit never reach our pods.
- ➖ It depends on the platform team having time before Nov 20. It must use the `cluster` or `redis` policy, not `local`. If it uses `redis`, that may be `redis-shared` again, which brings back the on-call approval. Responses use Kong's format, not ours.

**2. In the app, with a counter in Postgres**
- ➕ Our team owns it completely and ships it on our schedule. We control the 429 format. No approval from another team is needed.
- ➖ Every request adds one write to Postgres, and I can't size that load without traffic numbers. Under heavy load, rows for hot keys could contend. We'd also need a cleanup job for old counter rows.

**3. In the app, with a counter in `redis-shared`**
- ➕ Fastest per request. It's the standard pattern and simple to build.
- ➖ It needs on-call approval (INC-412 follow-up). Every request calls the Redis instance that already failed once. We'd have to decide what happens when Redis is down: allow everything or block everything.

## Recommendation and how sure I am

I'd go with **option 1: ask the platform team for Kong, and build option 2 as a fallback if they can't commit by a set date** (for example Nov 9, which leaves 11 days to build it). I'm **moderately sure, about 60%**. I'm confident about the reasoning: shared counting, no app code, no new load. But I couldn't confirm that Kong is in front of this API, how it authenticates, how many replicas there are, or where `handle()` lives. If any of those turn out wrong, the recommendation could change.

## Open questions

1. Which option do you want: 1, 2, or 3?
2. If you choose 1: should I plan it as a request to the platform team with a fallback to option 2, or should we build option 2 regardless?
3. If there's a fallback, what's the cutoff date for the platform team to commit? I'd suggest Nov 9.
4. Is Kong actually in front of these three `/v1` routes, and does Kong check the API keys (`consumer`) or does our app (`header`)?
5. Which counter policy does the platform team run, `cluster` or `redis`? If it's `redis`, is that `redis-shared`?
6. Roughly how many requests per second does the API handle at peak? I need this to size option 2's load on Postgres.
7. Should 429 responses use our own error format, or is Kong's default acceptable?
8. Where is the actual project code? This directory is empty, so I need the path or repo to check `api/app.py` and the deployment config before I plan anything.

---

## Run 3

all-decisions FAIL, decision-1 FAIL, facts PASS, no-trap-pick PASS, references FAIL; 1280 words

# Rate limiting for the `/v1` API: where should the limit live?

## What I checked first

I tried to verify the project before writing this, without changing anything. **I found nothing to check.** The working directory (`<sandbox>`) is empty. The parent folder has no `api/app.py`, Kong config, YAML or SQL. Searches for "rate limit", "kong", "redis-shared" and "INC-412" found nothing, and I'm not allowed to read my memory folder.

So every fact below comes from my earlier message in this session, and **I can't confirm any of it right now.** That affects how sure I can be (see the end).

## What we're doing and why it's needed now

We're adding a per-customer request limit to the public API: **100 requests per minute per API key**. It covers three `/v1` routes. I don't have their exact paths any more. Over the limit, the API returns **HTTP 429 Too Many Requests** with a **`Retry-After`** header that tells the client how many seconds to wait.

The launch is **Nov 20, 18 days from today (Nov 2)**. The decision is needed now because it decides **who builds this**: our team or the platform team. If it's another team, the request has to go in soon to fit their schedule.

## What each name and number means

| Term | Meaning |
|---|---|
| **6 replicas** | The API runs as 6 identical copies (pods), and a load balancer spreads requests across them. |
| **Counter in pod memory** | Each copy counts requests by itself. With 6 copies, one key could get about 6 × 100 = **~600/min**, so this approach is ruled out. |
| **`redis-shared`** | A Redis server (a fast in-memory store) that several services share. |
| **INC-412** | A past incident in which `redis-shared` failed. Its follow-up rule: **any new keys in `redis-shared` need on-call to agree first.** |
| **Kong** | The API gateway in front of our service. Every request goes through it before reaching our pods. |
| **Kong rate-limiting plugin** | Built-in Kong feature. `minute: 100` sets the limit. |
| **`limit_by: header` / `consumer`** | What Kong counts per caller. `header` counts per value of the `Authorization` header, which holds the API key. `consumer` counts per authenticated customer, but only works if Kong itself checks the API keys. |
| **Policy `local` / `cluster` / `redis`** | Where Kong keeps the counts. `local` keeps them in each Kong node's memory, which repeats the 6-replica problem if Kong has several nodes. `cluster` uses Kong's own database. `redis` uses a Redis server. |
| **`handle()` at `api/app.py:15`** | The function in our code where each request is processed. Options 2 and 3 would add the check there. |
| **Upsert** | One database statement meaning "insert this row, or add 1 if it already exists." |
| **Postgres** | Our main database. |

## Example: what happens when a client goes over the limit

Key `K` sends **150 requests in one minute**. The load balancer gives each of the 6 pods about 25.

| Approach | What the counter sees | Result |
|---|---|---|
| Counter in each pod's memory | Each pod sees ~25, below 100 | **All 150 succeed.** The limit doesn't work. |
| Kong with `local` policy, 3 Kong nodes | Each node sees ~50 | **All 150 succeed.** The limit doesn't work. |
| Kong `cluster`/`redis`, or options 2/3 | One shared count reaches 100 | Requests 1–100 succeed, **101–150 get 429** |

**What the customer sees** at request 101, if it arrives at 12:00:37:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 23
```

The options differ in the details:
- **Kong** sends its own body, `{"message":"API rate limit exceeded"}`, plus headers such as `X-RateLimit-Remaining-Minute: 0`. That's useful to clients, but it may not match our existing error format.
- **Options 2 and 3** let us write the body and headers, so they can match our other errors exactly.
- **All three options** use a fixed one-minute window. A client could send 100 requests at 12:00:59 and another 100 at 12:01:00, which is 200 in two seconds. That's normal for this kind of limit, but you should know about it.

## The options

### 1. Kong rate-limiting plugin (recommended)
**Pros**
- We write no app code.
- Postgres gets no extra load.
- Over-limit requests are rejected before they reach our pods.
- 429 and `Retry-After` are already built in.

**Cons**
- It depends on the platform team's schedule.
- It needs the `cluster` or `redis` policy, not `local`. `cluster` doesn't work if Kong runs without a database (DB-less) or on Konnect.
- If the policy is `redis` and that Redis is `redis-shared`, the INC-412 approval applies here too.
- The error format is Kong's, not ours.
- I haven't confirmed that Kong actually sits in front of these three routes.

### 2. In the app, counter in Postgres
**Pros**
- Our team owns it fully and ships it on our schedule.
- No new infrastructure and no approvals.
- We control the 429 format.
- We choose what happens if the counter fails: let requests through, or reject them.

**Cons**
- One extra write to Postgres on **every** request. If peak traffic is X requests/sec, that's X extra writes/sec.
- Writes for one busy key all compete for the same row.
- I can't estimate this load because I don't know our traffic.
- We need a cleanup job for old counter rows.

### 3. In the app, counter in `redis-shared`
**Pros**
- Fastest, and the most common way to do this.
- Very little load per request.
- We control the 429 format.

**Cons**
- Needs on-call to agree first (INC-412).
- Every API request then depends on the Redis that already failed once. If it fails again, we must either block all traffic or switch the limit off.

## My recommendation and how sure I am

**Ask the platform team for option 1 now, with a firm cutoff (for example Nov 10).** If they can't commit by then, build option 2, which fits in the remaining 10 days.

**How sure I am: moderately, about 60%.** Kong is the right place in general. But the recommendation depends on three things I couldn't check today:
- that Kong fronts these routes;
- which Kong mode it runs in, since that decides whether `cluster` is possible;
- which Redis the `redis` policy would use.

If any of these is false, I'd recommend option 2 instead.

## Open questions

1. **Which option: 1, 2 or 3?** If 1, do you agree to fall back to option 2 with a cutoff date, and which date?
2. **Where is the code?** This directory is empty. Give me the repo path and I'll re-check `api/app.py`, the replica count and the route names without changing anything.
3. **Does Kong sit in front of the three `/v1` routes?** Which mode does it run in: with a database, DB-less, or Konnect?
4. **Who checks API keys, Kong or our app?** This decides `consumer` vs `header`.
5. **If Kong uses the `redis` policy, which Redis would it be?** If it's `redis-shared`, does the INC-412 approval apply?
6. **What is the peak request rate on `/v1`?** I need it to size option 2's load on Postgres.
7. **If the counter store is down, should we let requests through or reject them?**
8. **Is 100/min the same for every key,** or do some customers need higher limits?
9. **Is the fixed one-minute window (up to 200 in two seconds at the boundary) acceptable?**
10. **Must the 429 response match our existing error format,** or is Kong's default body acceptable?
