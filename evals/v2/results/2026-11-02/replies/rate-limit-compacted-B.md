# rate-limit-compacted, cell B

## Run 1

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 500 words

**Context.** We're adding a rate limit to the public API for the Nov 20 launch, 18 days from today. Each API key gets at most 100 requests per minute, and any request past that is rejected with "429 Too Many Requests" plus a `Retry-After` header saying how long to wait. Nothing about the limit itself is still open. The one thing to decide is where requests get counted, because that decides which team does the work. I can't plan until that's settled.

Three facts shape the choice:
- The API runs as 6 copies (pods). If each copy counts only the requests it sees, one key could make about 600 requests a minute instead of 100. So the count has to be stored in one shared place.
- Our shared Redis cache (`redis-shared`) caused the INC-412 outage. Since then, on-call must approve any new use of it.
- Kong is the gateway every request passes through before it reaches our app. It has a built-in rate-limit feature.

**Options**

1. **Turn on Kong's rate limiting (the platform team does it)**
   - Pros: We write no code, because Kong already sends the 429 and `Retry-After`. It adds no load to our database.
   - Cons: It happens on the platform team's schedule, not ours. It also only works if they set Kong to keep one shared count across its servers (`cluster` or `redis` mode). The default mode, `local`, counts separately on each server and brings back the 600-per-minute problem.

2. **Count in our app, stored in Postgres (our team does it)**
   - Pros: We control it fully and can ship it on our own timeline.
   - Cons: It adds one extra database write to every API request. I can't tell from our code whether Postgres can handle that at launch traffic.

3. **Count in our app, stored in the shared Redis**
   - Pros: It's the fastest and most common way to do this.
   - Cons: It needs on-call's approval first. It also makes every request depend on the same Redis that caused the INC-412 outage.

**Recommendation: option 1, with option 2 as the backup (leaning).** The fact this depends on, and which I can't confirm because our repo has no Kong settings, is that the platform team can set this up in shared-count mode before Nov 20. The best case for option 2 is that we're never left waiting on another team. It still comes second because its cost, an extra database write on every request, is one I can't size, and option 1 has no such cost. If the platform team can't commit to a date within a few days, I'd switch to option 2. Option 3 is the weakest because it takes both the approval wait and the outage risk.

**The question:** Do you want (A) to ask the platform team for Kong rate limiting, building it ourselves in Postgres only if they can't do it by Nov 20, or (B) to build it ourselves in Postgres now, whatever their schedule?

---

## Run 2

all-decisions PASS, decision-1 PASS, facts PASS, no-trap-pick PASS, references PASS; 560 words

Here's the question again in plainer terms.

**Context.** We're adding a limit of 100 requests per minute for each API key on the three `/v1` endpoints. A client that goes over gets a "too many requests" error (HTTP 429) telling it how long to wait. The detailed plan, including who builds it, depends on **where the counting happens**. That's the only thing I need from you right now.

The count has to be shared. The app runs as 6 copies (pods), so if each copy counted on its own, one key could make 100 requests to each copy, up to about 600 a minute instead of 100.

Other constraints:
- Launch is **Nov 20**, 18 days from today.
- The shared Redis (`redis-shared`) is the cache that failed in incident INC-412. Since then, on-call has to approve any new use of it.

**Where we could count:**

| | Who builds it | Extra load per request | Done by Nov 20? |
|---|---|---|---|
| 1. Kong, the gateway in front of our app | Platform team | None on our systems | Depends on their schedule |
| 2. Our app, counting in Postgres | Us | One extra database write | Yes, we control the timing |
| 3. Our app, counting in `redis-shared` | Us, after on-call approves | One call to the Redis that failed in INC-412 | Depends on approval |

**Options**

1. **Kong** (the platform team turns on its built-in rate limiter)
   - Pros: we write no code, our database gets no extra work, and the 429 error and wait time are already built in.
   - Cons: the timing is in the platform team's hands. It also has to be set to share the count across Kong's servers ("cluster" or "redis" mode). If each Kong server counts separately, we have the 600-a-minute problem again.
2. **Postgres counter in our app** (one row per key per minute, added to or created on each request)
   - Pros: we own it completely and can ship on our own schedule.
   - Cons: it adds a write to Postgres on every request, and I can't tell from the code whether Postgres can handle that at our traffic.
3. **Redis counter in our app**
   - Pros: it's the fastest and most common way to do this.
   - Cons: it needs on-call approval, and it makes every request depend on the Redis that already failed once.

**Recommendation:** Kong, with Postgres as the backup. This is a lean, not a firm call. Kong costs us no code and adds no load. The strongest argument against it is that we don't control its timing. A fixed deadline for the platform team handles that. If they can't commit by around Nov 10, we build the Postgres version ourselves, which still leaves about 10 days.

Two things I couldn't check would change my mind. One is whether the platform team can fit this in before Nov 20. The other is which mode their Kong uses. Neither is set up anywhere in this repo.

**Which do you want?**
- **A.** Ask the platform team for Kong, and build the Postgres version ourselves if they can't commit by about Nov 10.
- **B.** Build the Postgres version ourselves from the start, so we don't depend on them.
- **C.** Use Redis, if you'd rather ask on-call for approval.

---

## Run 3

all-decisions PASS, decision-1 PASS, facts PASS, no-trap-pick PASS, references FAIL; 472 words

Here's the question again in plainer terms.

**Context**

We're adding a limit to the public API: each API key can make at most **100 requests per minute**. After that, callers get a "too many requests" error that tells them how long to wait. This needs to be live for the launch on **Nov 20**, which is 18 days away. I can't write the detailed plan until we decide **where the counting happens**.

Some facts that rule things out:
- The API runs as **6 copies** at once. If each copy kept its own count, a key could get 100 requests through each copy, which is about 600 a minute in total. So the count has to be stored in one shared place.
- We have a shared Redis server (a fast in-memory store) called `redis-shared`. After a past outage of that server (INC-412), on-call must approve any new use of it.
- I'm assuming the limit applies only to our three `/v1` endpoints.

**Options**

1. **Have the gateway enforce it.** Kong is the gateway that sits in front of our API, and it has a built-in rate limiter. The platform team would switch it on.
   - Pros: we write no code; it already sends the right error; our database takes no extra load.
   - Cons: it depends on the platform team's schedule, which we don't control. They also need to set it to count across all gateway machines, not separately on each one, or the 600-a-minute problem comes back.

2. **Enforce it in our app, with the count kept in our Postgres database.**
   - Pros: our team owns it end to end and can ship it on our own schedule.
   - Cons: every API request adds one database write. I can't tell from the code whether the database can handle that at launch traffic.

3. **Enforce it in our app, with the count kept in `redis-shared`.**
   - Pros: it's the fastest option and the most common way to do this.
   - Cons: it needs on-call's approval, and every request would depend on the same server that caused INC-412.

**Recommendation: option 1, with option 2 as the fallback (leaning, not certain).** It's the least work and puts no new load on anything we run. The best argument for option 2 is that we wouldn't depend on another team with only 18 days left. That risk goes away if we ask the platform team now and set a deadline: if they can't commit by about **Nov 9**, we build option 2. One fact I can't check from here is whether they can deliver in time. If they say no, my recommendation becomes option 2.

**Which do you want: (a) ask the platform team for Kong, with Postgres as the fallback; (b) build the Postgres version now no matter what; or (c) the Redis version?**
