# vector-index-unsure, cell C

## Run 1

all-decisions FAIL, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 1601 words

# MOSS-311: where to search the help-center vectors (restart from scratch)

**I couldn't re-check the project just now.** Read, Glob and Grep were all denied in this session ("don't ask" mode). Every fact below comes from my earlier reading of the repo in this conversation, not from a fresh check. Where a fact matters, I give the file and line I read it from so you can confirm it.

## What we're doing and why the decision is needed now

Mossline's help-center search only matches words. A customer who types "can't log in" gets nothing, because the article that would help is called "Resetting your password". Ticket **MOSS-311** asks for search that matches meaning, shipped in the **December release**. The vectors needed for this are already computed every night. What's left is deciding **where they're searched** and **with what kind of index**.

This needs deciding now because one option depends on another team (the data team) changing the database. It's 2 November, and if that change can't land before December, we have to build the other option.

## What every code, number and name means

| Term | Meaning |
|---|---|
| **Mossline** | Our product: a support desk. Support agents answer tickets, and customers read each company's help center. |
| **Tenant** | One customer company with its own help center. Today there are 1,340. |
| **MOSS-311** | The open ticket: search by meaning. |
| **MOSS-298** | The closed ticket that added the nightly embedding job (`search/embed_corpus.py`). |
| **mossline-api** | Our Python API service. It runs as 4 pods (copies), each capped at 1280 MiB of memory (`deploy/api.yaml`). |
| **Postgres 14, primary + read replica** | The database. The replica is a read-only copy, which the data team's reporting dashboards also read. |
| **Data team** | Runs Postgres. Any schema change or extension goes through their review (`docs/ARCHITECTURE.md`). |
| **Platform team** | Sets pod memory. They agreed search may add at most **256 MiB per pod**. Anything more needs a capacity request, and the next review is in **February** (`config/search.yaml:17`). |
| **`articles.tsv`** | The word index today's search uses (Postgres full-text search, `search/keyword.py`). |
| **embed-m2** | The hosted embedding API we already pay for. It turns text into a list of 768 numbers (a **vector**). Similar meanings give nearby vectors. |
| **Chunk** | A 200-word slice of an article. Each chunk gets its own vector. |
| **`chunk_vectors`** | The table holding those vectors as raw bytes. Nothing reads it yet. |
| **float32 / int8** | 4 bytes or 1 byte per number. One vector is 3 KiB in float32. |
| **212,000 chunks / 621 MiB** | The whole corpus today: 212,000 × 768 × 4 bytes of raw vectors. |
| **~160 chunks per tenant** | My average: 212,000 ÷ 1,340. It's an **average**, and the largest tenant isn't known. |
| **p95 ≤ 150 ms** | 95% of searches must finish within 150 ms, because results refresh as the customer types. |
| **Exact search** | Compare the query against every vector of that tenant. It's always correct and needs no index. |
| **ANN / HNSW** | Approximate nearest-neighbour search. HNSW is the common graph index for it. It's fast on huge sets but can miss results. |
| **pgvector** | The Postgres extension that adds a `vector` type, distance operators and HNSW indexes. |
| **LRU cache** | An in-memory cache that evicts whatever was used least recently once it's full. |
| **Enterprise tier** | Opens in Q1 2026–27. Expect "a few large tenants", sizes unknown. |

## Already settled (not the decision)

**Index type: exact search inside the tenant for now. No global ANN index.**
- At about 160 chunks, an exact comparison takes microseconds and never misses a result.
- One shared HNSW index over all 212,000 chunks would break the tenant rule. Each tenant is about 0.07% of it, so the nearest neighbours the graph finds are mostly other tenants' chunks. After filtering by tenant, few or none are left.
- An ANN index only becomes necessary for a single very large tenant. Then it would be an index for **that tenant only**.

## The decision: where the search runs

**Option A: inside Postgres, using pgvector.** The data team installs pgvector, converts `vec` to `vector(768)`, and adds an index on `tenant_id`. The API sends one query to the replica. Exact search covers today's tenants, and a per-tenant HNSW index can be added later for large Enterprise tenants.

**Option B: inside the API pods, with no database changes.** On a tenant's first search, a pod loads that tenant's vectors from `chunk_vectors`. It keeps them in an LRU cache capped below 256 MiB and compares them in Python/numpy.

(Option C, loading all vectors into every pod, is ruled out: 621 MiB is more than the 256 MiB budget.)

### Live example (illustrative numbers, nothing benchmarked)

A customer of an average tenant (~160 chunks) types "can't log in":
- **Today:** no words match, so the result is 0 articles.
- **A and B:** both embed the query with embed-m2 and compare it against the tenant's ~160 chunks. The best chunk of "Resetting your password" scores highest, so that article is returned first. **For today's tenants, A and B return identical results**, because both do exact search.

The difference shows up with a large Enterprise tenant, say 100,000 chunks (about 290 MiB in float32):
- **A:** that tenant gets its own HNSW index in Postgres, and search stays fast.
- **B:** its vectors alone exceed the 256 MiB cache. That tenant either can't use meaning-based search in the pods, or we have to rebuild before Q1.

### UX example: what a customer sees

A customer types "c… ca… can't… can't log in" and the list refreshes with each keystroke.
- **A:** each refresh is one database query plus the embed-m2 call. Performance is the same for every tenant and every pod.
- **B:** after a deploy or pod restart, the first refresh for a tenant on that pod waits while its vectors load. For a small tenant (~470 KiB) that's probably barely noticeable. For a large tenant it would be visibly slow or wouldn't work. Each of the 4 pods warms its cache separately, so the same customer may see different speeds from one request to the next.
- **Both:** every keystroke calls embed-m2 over the network. I don't know that call's latency, and it could take up most of the 150 ms in either option.

### Pros and cons

| | **A: Postgres + pgvector** (recommended, if the date holds) | **B: in-pod cache** |
|---|---|---|
| **Pros** | No pod memory needed. Scales to Enterprise with per-tenant HNSW. One source of truth, always up to date with the nightly job. Standard and well known. | No dependency on the data team (except maybe a `tenant_id` index). Can start immediately. Database load is just one read per tenant per pod. |
| **Cons** | December depends on a review and migration we don't control. Search load shares the replica with the dashboards. Converting `vec` is a migration on a live table. | Cold-cache slowdowns. Can't hold a large Enterprise tenant within 256 MiB, so probably needs replacing by Q1. Similarity search code we write and maintain ourselves. A cache can drift from the table between nightly runs. |

## Recommendation and how sure I am

**Go with A if the data team commits to the pgvector change by about mid-November. Otherwise build B for December and move to A before Enterprise launches.**

It rests on three facts, which I read earlier but couldn't re-check just now:
1. 621 MiB raw is more than the 256 MiB per-pod budget, and the next capacity review is in February (`config/search.yaml:12,17`).
2. Extensions and schema changes go through the data team (`docs/ARCHITECTURE.md`).
3. Nothing I read shows an index on `chunk_vectors.tenant_id`. The upsert only implies a unique key on `(article_id, n)`. I did **not** search the whole repo for migrations, so one could exist outside the folders I read.

How sure I am:
- **High:** exact per-tenant search over a global ANN index. That's arithmetic from the repo's numbers.
- **Medium:** A over B. It hinges on the data team's timeline, which I don't know.
- **Low:** meeting 150 ms in either option. embed-m2 latency and replica load aren't in the repo, and nothing has been benchmarked.

Separately, one bug applies to both options: the nightly job only inserts and updates, never deletes. Chunks from shortened or deleted articles stay in `chunk_vectors` and would show up as results.

## Open questions (all of them)

1. **Can the data team install pgvector, convert `vec` to `vector(768)` and add a `tenant_id` index before December? By what date?** This is the one that decides A or B.
2. What's the exact December release date or code freeze?
3. May interactive search traffic run on the read replica alongside the dashboards, or does the data team want it elsewhere?
4. Do we know the size of the largest current tenant (chunks or articles), not just the average?
5. Do we have any size estimate or start date for the first Enterprise tenants?
6. Is there a known latency or rate limit for embed-m2 at one call per keystroke? May we debounce, e.g. wait 150–200 ms after typing stops?
7. If meaning-based search is slow or unavailable, is falling back to today's keyword search acceptable?
8. Should fixing the stale-chunk bug in the nightly job be part of MOSS-311, or a separate ticket?

---

## Run 2

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 1570 words

# MOSS-311: where to search the help-center vectors (the decision, restated from scratch)

**I couldn't re-check the project just now.** Every file read was denied in this turn ("don't ask" mode), so nothing could be opened or changed. Everything below comes from the files I read earlier in this session: `TICKETS.md`, `docs/`, `config/search.yaml`, `search/`, `deploy/api.yaml`. If you want the facts re-checked, allow Read on `/work` and I'll do it before you decide.

## What we're doing and why it needs deciding now

Customers search a company's help center in their own words and often get nothing. "can't log in" finds no article because the right one is titled "Resetting your password". MOSS-311 asks for search that matches meaning. The vectors that make this possible already exist, but nothing reads them.

The open question is **where those vectors get searched**. One option is inside our Postgres database, which needs another team to change it. The other is inside our own API servers, which needs nobody. The deadline is the December release. If we pick Postgres, the other team's review has to start now or it may not land in time.

## What each code, number and name means

| Item | Meaning |
|---|---|
| **Mossline** | Our product, a support desk. Each customer company (**tenant**) has its own help center. |
| **MOSS-311** | The ticket for meaning-based help-center search. |
| **MOSS-298** | The closed ticket that added the nightly job creating the vectors. |
| **`search/keyword.py`** | Today's search: Postgres word matching on `articles.tsv`, one tenant only, top 10 articles. |
| **`search/embed_corpus.py`** | The nightly job. It splits each article into **200-word chunks**, turns each chunk into a vector, and saves it. It only inserts or updates; it never deletes old chunks. |
| **`chunk_vectors`** | The Postgres table holding those vectors (`article_id, tenant_id, n, vec`). `vec` is stored as raw bytes, not a searchable vector type. |
| **embed-m2** | The hosted embedding API we already pay for. It turns text into **768 numbers** (float32, 4 bytes each). Every search needs one call to it to turn the customer's query into a vector. |
| **vector / embedding** | That list of 768 numbers. Texts with similar meaning get similar vectors. |
| **pgvector** | A Postgres extension that adds a vector column type and vector search. We don't have it installed. |
| **ANN / HNSW** | Approximate nearest-neighbour index, used to search millions of vectors quickly. HNSW is the common kind. **Exact search** means comparing against every vector instead. |
| **data team** | Runs Postgres (one primary, one read replica). Extensions and schema changes need their review. Their reporting dashboards read the same database. |
| **platform team** | Agreed the memory budget for our API servers. |
| **`mossline-api`** | Our API service, **4 pods** (copies). Each is capped at **1280 MiB** of memory (`deploy/api.yaml`). |
| **1,340 / 18,400 / 212,000** | Tenants / articles / chunks, counted 2026-10-31. |
| **621 MiB** | Size of all vectors raw: 212,000 × 768 × 4 bytes. |
| **~160 chunks, ~470 KiB** | An average tenant: 212,000 ÷ 1,340 chunks. That's an average only; the repo doesn't show the largest tenant. |
| **256 MiB** | The most extra memory search may add to *each* pod. More needs a capacity request, and the next review is **February**. |
| **150 ms p95** | 95% of search calls must finish within 150 ms. Results refresh as the customer types. |
| **Enterprise / Q1** | A new tier opening in Q1. Sales expects "a few large tenants", sizes unknown. |
| **~155 MiB (int8)** | The vectors if shrunk to 1 byte per number. |
| **~290 MiB** | My example of a hypothetical 100,000-chunk tenant. |

## What's already settled (both options share it)

Every search covers only one tenant, about 160 chunks on average. Comparing a query against 160 vectors exactly takes microseconds and never misses a match. So **we don't need an ANN index for December.**

A single big HNSW index over all tenants would actually make results worse. Each tenant is only about 0.07% of that index, so its nearest neighbours are mostly other tenants' chunks. Once those are filtered out, the search returns few or no results. Large tenants can get their own index later, if one ever needs it.

Both options work the same way: score every chunk of the tenant, take each article's best chunk, and return the top 10 articles.

## Live example: tenant "Acme", ~160 chunks, customer types "can't log in"

- **Today:** Postgres looks for the words in article text. "Resetting your password" doesn't contain them, so the customer sees no results.
- **Option A (Postgres + pgvector):** API → embed-m2 turns the query into a vector → one SQL query on the replica, `WHERE tenant_id = Acme ORDER BY distance LIMIT …` → top chunks grouped by article → 10 titles. "Resetting your password" comes first.
- **Option B (in our pods):** API → embed-m2 → is Acme's set of vectors already in this pod's memory? If not, read Acme's ~470 KiB from `chunk_vectors` and keep it. Then compare in the pod → same 10 titles, same order.

**What the customer sees (UX example).** Normally, nothing differs: both options do exact search, so they return the same list. The differences show up in edge cases:

| Situation | A | B |
|---|---|---|
| First search for Acme after a pod restart, or after Acme's vectors were dropped from memory | normal speed | that first keystroke is slower because it loads Acme's vectors first (how much slower is unknown) |
| Large Enterprise tenant (e.g. 100k chunks ≈ 290 MiB) | works; add an HNSW index just for that tenant if it's slow | **doesn't fit** in the 256 MiB budget: slow results, or we have to fall back to keyword search |
| Article edited last night | new text searchable after the nightly job | same, *plus* a pod may keep the old version in memory until it reloads (needs an expiry time) |
| Article deleted or shortened | **both:** old chunks stay in the table and can show up as results, leading the customer to a dead link. This is the nightly job's missing delete, not this decision. | same |

## The options

**A. Search in Postgres with pgvector.** This is my recommendation *if the data team can deliver in time*.
- **Pros:**
  - No extra pod memory.
  - Scales to Enterprise with a per-tenant HNSW index.
  - One copy of the data, so pods never hold stale vectors.
  - Simplest app code: one SQL query.
- **Cons:**
  - December depends on the data team's review plus a migration: install the extension, convert `vec` to `vector(768)`, add a `tenant_id` index.
  - Search load lands on the replica the dashboards also read, and the repo doesn't say how much it can take.

**B. Search inside the API pods, with Postgres unchanged.** This is my recommendation *if A can't be ready*.
- **Pros:**
  - Doesn't need the data team (except possibly a `tenant_id` index).
  - Fits the 256 MiB budget for today's tenants: each pod caches only the tenants searched recently.
  - Adds no new load on the database beyond the loads when a tenant isn't yet cached.
- **Cons:**
  - Each pod keeps its own copy: more code (cache, expiry, memory cap) and possibly stale data.
  - The first search after a cache miss is slower.
  - One large Enterprise tenant can break the budget, so it probably has to be replaced by A in Q1. That means building search twice.

**Considered and rejected:**
- **Load all vectors into every pod:** 621 MiB is more than the 256 MiB budget.
- **Shrink them to int8 (~155 MiB) and load all:** fits today, but leaves no room for growth or for HNSW overhead.
- **A separate vector database service:** a new system plus a capacity request is too much to get done by December.

## How sure I am

- **High** that exact search per tenant is enough for today's *average* tenant. That's arithmetic on the config numbers.
- **Medium** for the largest *current* tenant. The repo only gives totals, and one tenant could be far above 160 chunks.
- **Low** on the 150 ms target. The embed-m2 call counts against it in both options, and its latency isn't stated anywhere.
- **The A-vs-B choice rests on one fact that isn't in the repo:** whether the data team can ship the pgvector change before December.

## Open questions, all at once

1. Can the data team review and ship pgvector by mid-November (extension, `vec` → `vector(768)`, `tenant_id` index)? Or should I assume Postgres stays unchanged?
2. Is it OK for search queries to run on the read replica the dashboards use?
3. How many chunks does the largest tenant have today? Can someone run a count per tenant on `chunk_vectors`?
4. Do we know embed-m2's response time or SLA?
5. Does Sales have even a rough size for the large Enterprise tenants (number of articles)?
6. If embed-m2 is slow or down, should the search box fall back to today's keyword search?
7. Should MOSS-311 also fix the nightly job so it deletes chunks of edited or deleted articles?
8. What's the exact date of the December release?

---

## Run 3

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 1593 words

# MOSS-311: where to run vector search (re-brief)

**I couldn't re-check the project just now.** This turn, Read, Grep and Glob were all denied by the permission mode, so nothing was opened or changed. The facts below are from the files as I read them earlier in this session. If you allow read access again, I'll re-confirm them.

## What we're doing and why the decision is needed now

Customers search the help center in their own words and often get nothing. The ticket asks for search that matches what they mean. The vectors for that are already built every night, but nothing searches them yet. Before writing any code we have to choose **where that search runs**:

- **In the database**, which needs changes from the data team.
- **Inside our API servers**, which needs nothing from them.

This has to be decided now because the database route depends on another team's review, and the release is in December. If we wait until mid-November to find out they can't make it, there's no time left for the other route.

## Glossary: every code, number and name

| Term | Meaning |
|---|---|
| **Mossline** | Our product: a support desk. Each customer company (a **tenant**) has its own help center of articles. |
| **MOSS-311** | Open ticket: meaning-based help-center search, due in the December release. Product notes are in `docs/semantic-search-prd.md`. |
| **MOSS-298** | Closed ticket that added `search/embed_corpus.py`, the nightly job that creates the vectors. |
| **embed-m2** | The hosted embedding API we already pay for. It turns text into a list of 768 numbers (a **vector**). Texts with similar meaning get similar vectors. |
| **768 dimensions, float32** | Each vector is 768 numbers at 4 bytes each, so 3 KiB per vector. |
| **chunk** | A 200-word piece of an article. The job embeds each chunk separately. |
| **`chunk_vectors`** | Postgres table holding `(article_id, tenant_id, n, vec)`. `n` is the chunk number and `vec` is stored as raw bytes, not a native vector type. |
| **`articles.tsv`** | The word index today's keyword search uses (`search/keyword.py`). |
| **`mossline-api`** | Our Python API service: 4 **pods** (copies), each capped at **1280 MiB** of memory (`deploy/api.yaml`). |
| **256 MiB** | The most memory search may add to *each* pod, agreed with the platform team in October. More needs a capacity request, and the next review is in **February**. |
| **p95 ≤ 150 ms** | 95% of search calls must finish within 150 milliseconds, because results refresh as the customer types. |
| **1,340 / 18,400 / 212,000 / 621 MiB** | Tenants, articles, chunks, and total raw vector size, counted 2026-10-31 (`config/search.yaml`). |
| **~160** | Average chunks per tenant (212,000 ÷ 1,340 ≈ 158), about 475 KiB per tenant. |
| **Postgres 14, primary + read replica** | Our database, run by the **data team**. The replica is a read-only copy that the data team's dashboards also use. Extensions and schema changes need their review. |
| **pgvector** | A Postgres extension that adds a vector column type and vector search. |
| **Exact search** | Compare the query with *every* vector of the tenant. Always finds the true best matches. |
| **ANN / HNSW** | Approximate nearest-neighbour search. HNSW is the usual index for it. It's fast on huge sets but can miss results, especially when combined with a "this tenant only" filter. |
| **LRU cache** | A memory cache that evicts whatever was used least recently once it's full. |
| **Enterprise tier, Q1** | A new plan launching next quarter. Sales expects "a few large tenants", with no sizes given yet. |

## Live example: the same query today and after MOSS-311

Tenant 42 has an article titled "Resetting your password". A customer types **"can't log in"**.

- **Today:** Postgres reduces the query to the word stem `log` (other words like "can't" are dropped as too common). It looks for that stem in `articles.tsv`. The article doesn't use that word, so the result is **0 matches**. The ticket describes exactly this case.
- **After MOSS-311 (both options):**
  1. embed-m2 turns "can't log in" into a vector.
  2. We compare it with tenant 42's ~160 chunk vectors.
  3. Each article is scored by its best chunk, and we show the top 10.
  
  A chunk like "If you can't sign in, reset your password…" is close in meaning, so "Resetting your password" comes out on top. *(The article text here is illustrative; I haven't seen real article bodies.)*

## UX example: what customers would see differently

For most tenants the **results are identical** under both options, because both use exact search. The differences are in timing and freshness:

| Moment | A: search in Postgres | B: search in API pods |
|---|---|---|
| First search for a tenant | Normal speed | That pod first loads the tenant's vectors. Fast for 160 chunks; a large tenant could see a slow first keystroke. |
| Article edited today | New text is searchable after the nightly job | Same, plus however long the pod keeps its cached copy |
| A large Enterprise tenant in Q1 | Still fast once it gets its own index | May exceed the cache, making searches slow or forcing a fallback |
| Dashboard reports running heavily | Searches may slow down (shared replica) | Not affected |

Under **both** options there's one problem: the nightly job never deletes old chunks. A deleted article could still show up in results, and clicking it gives a "not found" page.

## Options

**A. Search in Postgres with pgvector.** The data team installs pgvector, converts `vec` to a vector column, and adds a `tenant_id` index. Queries run on the replica: exact search per tenant now, and a dedicated HNSW index for any very large tenant later.
- ✅ Scales to Enterprise without touching pod memory, and no new infrastructure on our side.
- ✅ Data stays in one place with nothing to keep in sync.
- ❌ December depends on the data team's review and migration, which we don't control.
- ❌ Shares the replica with dashboards, and I can't tell from the repo how much load it can take.

**B. Search inside the API pods; Postgres unchanged.** Each pod loads a tenant's vectors from `chunk_vectors` the first time that tenant searches. It keeps them in an LRU cache under 256 MiB and scores them exactly in Python/numpy.
- ✅ No dependency on the data team (except maybe a `tenant_id` index, if one doesn't exist).
- ✅ Doesn't add load to the shared replica after the first load.
- ❌ One large Enterprise tenant could fill the cache, so this probably needs replacing by Q1.
- ❌ Four separate caches mean slow first loads and stale copies to manage.

**C. A separate vector search service or database.** Considered for completeness.
- ✅ Not limited by the per-pod budget, and scales well.
- ❌ New infrastructure to run and secure, which likely needs a platform capacity request (February) before December. Too slow for this release.

**Ruled out: a full copy of all vectors in every pod.** 621 MiB is about 2.4 times the 256 MiB budget. Shrinking the vectors (int8, ~155 MiB) fits today but leaves almost no room for growth.

**Ruled out: one global ANN index with a tenant filter.** Each tenant is about 0.07% of the data, so the index mostly finds other tenants' chunks, and filtering then leaves few or no results.

## Recommendation and the fact behind it

**A, if the data team can commit by mid-November. Otherwise B for December, then move to A before Enterprise launches.**

This rests on one fact: **tenants are small, so exact per-tenant search is cheap anywhere.** From `config/search.yaml` as read earlier: 212,000 chunks across 1,340 tenants, about 160 each. The arithmetic checks out: 212,000 × 768 × 4 bytes is 621 MiB, matching the file. But that's an **average**. The repo has no breakdown by tenant, so one tenant today could already be much larger. The repo also has no schema files, so I can't confirm whether `chunk_vectors` has a `tenant_id` index. The only key I saw is `(article_id, n)`, implied by the upsert.

**How sure I am:**
- **High** on ruling out the global ANN index and the full in-pod copy (simple arithmetic).
- **High** that exact search per tenant is the right method for December.
- **Medium** on A vs B. That depends on the data team's timeline and the replica load, neither of which is in the repo.
- **Low** on whether 150 ms is achievable at all, because embed-m2's response time per query is unknown and comes out of that budget in every option.

## Open questions

1. Can the data team install pgvector, convert `vec`, and add a `tenant_id` index on the replica **before mid-November**? Is pgvector even available on their Postgres 14 setup?
2. Does the **150 ms p95** include the embed-m2 call, or only our search? Do you know embed-m2's typical response time?
3. How many chunks does the **largest current tenant** have? Is there any rough upper size for the Enterprise tenants?
4. Is it acceptable to put search load on the **read replica the dashboards use**?
5. Should fixing the **deleted-article gap** in the nightly job be part of MOSS-311?
6. Should meaning-based search **replace** keyword search, or run **alongside** it (e.g. so exact terms like error codes still match)? The PRD rules out reranking but doesn't say.
