# rate-limit-compacted, cell A

## Run 1

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references FAIL; 265 words

Sure, here's the short version.

**What we're deciding:** where the "100 requests per minute per API key" limit should live.

**Why it isn't simple:** the app runs as 6 copies. If each copy counts requests on its own, one key could make 100 requests to each copy, which is 600 a minute. So the count has to be kept in one shared place.

**The three choices:**

1. **Have the gateway do it (Kong).** Kong is the front door that every request already passes through, and it has a built-in rate limit feature. The platform team switches it on and we write no code. The downside is that we depend on them getting it done before the Nov 20 launch.

2. **We build it, and keep the count in our Postgres database.** Our team controls it fully and can ship it on our own schedule. The downside is one extra database write on every request, and I can't tell from the code how much load that adds.

3. **We build it, and keep the count in the shared Redis.** This is the usual way to do it and it's fast. But on-call has to approve it first, and that Redis is the one involved in the recent outage (INC-412).

**My suggestion:** ask the platform team for option 1, and switch to option 2 if they can't commit to finishing before Nov 20.

**What I need from you:**
- Are you OK with that plan (1, with 2 as a backup)?
- Or would you rather do option 2 now so we don't depend on anyone else?

---

## Run 2

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references FAIL; 253 words

Sure, here it is more simply.

**The question:** Where should the "100 requests per minute per API key" limit live?

**Why we have to choose:** We run 6 copies of the app. If each copy keeps its own count, a key could get about 600 requests a minute. All the copies need to share one count, and there are three places that count could live.

**The three choices:**

1. **Kong (the gateway in front of our app).** The platform team turns on Kong's built-in rate limiter. We write no code. The downside is that we depend on the platform team getting it done before the Nov 20 launch.
   *This is what I recommend.*

2. **Our app, keeping the count in Postgres.** We build it ourselves and control the timing. The downside is that every request adds one more write to the database, and I can't tell from the code whether the database can handle that.

3. **Our app, keeping the count in the shared Redis.** This is the fastest and most standard way. The downside is that on-call has to approve it first, and it's the same Redis that caused the INC-412 outage.

**What I need from you:** pick one of these.

- **A:** Go with Kong (option 1), but fall back to building it ourselves in Postgres (option 2) if the platform team can't finish in time.
- **B:** Build it ourselves in Postgres (option 2) now, so we don't have to wait on anyone.
- **C:** Something else, like option 3.

---

## Run 3

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references FAIL; 230 words

Sure, here it is more simply.

**What we're building:** a rule that each API key can make at most 100 requests per minute. Extra requests get turned away with a "slow down" reply.

**The problem:** our app runs as 6 copies. If each copy keeps its own count, a key could get 100 requests from each copy, so 600 a minute. The count has to live somewhere all the copies share.

**Three places it could live:**

1. **The gateway in front of our app (Kong). This is what I recommend.** The platform team switches on a built-in setting. We write no code. The downside is that we depend on their schedule.
2. **Our own database (Postgres).** We write the code ourselves and control the timing. The downside is an extra database write on every request, and I can't tell how much load that adds.
3. **The shared Redis cache.** This is the usual fast option. But on-call has to approve it first, and it's the same Redis that broke in the recent incident (INC-412).

**What I need from you:** we launch Nov 20, which is 18 days away. Which of these two do you want?

- **A)** Ask the platform team for option 1, and if they can't finish by Nov 20, build option 2 ourselves.
- **B)** Build option 2 ourselves now, so we don't depend on anyone else.
