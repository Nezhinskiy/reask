# vector-index-unsure, cell D

## Run 1

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick FAIL, references PASS; 902 words

# MOSS-311: where to run the vector search

**Context.** Mossline is a support desk, and each customer company (a "tenant") has its own help center. Help-center search today only matches the exact words typed. So a customer who types "can't log in" gets nothing, because the article is titled "Resetting your password". **MOSS-311** is the ticket to make search match meaning, due in the December release. That's about four weeks away; today is 2 Nov.

The ingredients already exist. **MOSS-298**, a closed ticket, added a nightly job. It splits every article into 200-word chunks and turns each chunk into a **vector** (768 numbers that encode its meaning) using **embed-m2**, the paid embedding service. It stores them in the **`chunk_vectors`** table in our Postgres database. Nothing reads that table yet. The database is run by the data team, and any new extension or schema change goes through their review. It also has a read-only copy (a **replica**) that the data team's dashboards also use.

Product requirements:
- results update as the customer types;
- **p95 ≤ 150 ms**, meaning 95% of searches finish within 150 ms;
- each tenant sees only its own articles.

The platform team has capped the extra memory search may add to each of the 4 **`mossline-api`** pods (the servers that answer requests) at **256 MiB**. Raising that cap needs a capacity request, and the next review is in February. An **Enterprise tier** with "a few large tenants" opens in Q1, sizes unknown.

**Decided:** nothing yet.

**My assumption, carried over:** for each query we compare it against every chunk the tenant has (**exact search**) and return the 10 best articles. The average tenant has about **160 chunks** (212,000 chunks ÷ 1,340 tenants, counted 31 Oct), which takes microseconds to scan. A shared shortcut index across all tenants (**ANN**, approximate nearest-neighbour search, such as **HNSW**) works badly here. Each tenant is only about 0.07% of that index, so after filtering to one tenant it often returns few or no results.

What waits on this decision is the whole build: where the code lives, and whether we need a migration from the data team.

**Live example.** What customers see is identical under both options: "can't log in" returns "Resetting your password". The options differ in what happens as tenants grow:

| | Average tenant today (160 chunks, about 0.5 MiB) | Large Enterprise tenant, hypothetical 100k chunks (about 290 MiB) |
|---|---|---|
| **A: in Postgres** | Fast scan on the replica | Gets its own small HNSW index; results stay fast |
| **B: in the pods** | Loaded once, then fast in memory | Bigger than the whole 256 MiB cache, so that tenant's search is slow or fails |

## Options

**A. Search inside Postgres using pgvector** (a Postgres extension that adds a vector column type and vector indexes). The data team would install it, convert the stored vectors from raw bytes to that type, and add an index on `tenant_id`. Queries run on the replica.
- Pros: handles Enterprise tenants by giving each large one its own index (a "partial" HNSW index); no extra pod memory; one copy of the data, always current.
- Cons: December depends on a review and migration we don't control; per-keystroke search adds load to the replica the dashboards use.

**B. Search inside the API pods; Postgres unchanged.** Each pod loads a tenant's vectors the first time that tenant searches, keeps them in a cache capped under 256 MiB (least-recently-used tenants get dropped), and compares them in memory.
- Pros: no dependency on the data team, so December is in our hands; barely touches the database.
- Cons: one large Enterprise tenant breaks it, so it probably gets replaced in Q1, meaning the work is done twice; the cache has to be refreshed after each nightly job, or it serves yesterday's articles.

## Recommendation

**Leaning toward A if the data team commits by mid-November, otherwise B now and A for Q1.**

It all turns on one fact: **can the data team ship pgvector before December?** That's not recorded anywhere in the project. None of the seven files mentions pgvector or a migration. I couldn't search the rest of the repo this session (the search tools were blocked), so treat that last point as unchecked.

The strongest case against A: with four weeks left, a review nobody has requested yet is the likeliest thing to make us miss December. B removes that risk for everything today's tenants need. That's why the fallback exists. But A is what Enterprise needs anyway, so if it can land in time, building B first is wasted work.

Two more unknowns. Neither changes A vs B, but both affect the plan:
- **embed-m2's response time per query.** Both options have to fit it inside the 150 ms.
- **Size of the largest current tenant.** The 160 figure is an average. If one tenant is already huge, B is riskier than it looks.

## Questions

1. **Can the data team install pgvector and migrate `chunk_vectors` before the December release?** (Yes, committed → A / No → B / Don't know → B for now, and I'd draft the request to the data team for you to send.)
2. Do you know embed-m2's typical response time for a short query? (Number / Unknown)
3. Do you know how many chunks or articles the largest current tenant has? (Number / Unknown)

---

## Run 2

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 909 words

# MOSS-311 vector search: where the vectors are searched

**Context.** Mossline is a support-desk product. Each customer company (a "tenant") has its own help center. Right now help-center search only matches exact words. It's a Postgres full-text query in `search/keyword.py`, so a customer who types "can't log in" doesn't find the article "Resetting your password". **MOSS-311** is the ticket to make search match meaning instead, due in the December release (about four weeks from today, 2 Nov 2026). The vectors it needs already exist. A vector is a list of 768 numbers that represents what a piece of text means, so texts with similar meanings get similar vectors. **MOSS-298** (closed) added a nightly job that splits every article into 200-word chunks, gets a vector for each chunk from **embed-m2** (the hosted embedding service we already pay for), and stores the vectors in the Postgres table **`chunk_vectors`**. Nothing reads that table yet. I haven't written any code. Choosing where the search runs is the next step.

**Decided** (from `docs/semantic-search-prd.md` and `config/search.yaml`):
- Results refresh as the customer types, and **p95** must be ≤ 150 ms (95% of searches finish within 150 ms).
- Each tenant searches only its own articles.
- Each **`mossline-api`** pod (we run 4 copies of the Python API server) may use at most 256 MiB more memory. Asking for more means a capacity review, and the next one is in February.

**Settled by arithmetic on the repo's numbers:**
- 212,000 chunks across 1,340 tenants is about **160 chunks per tenant on average**. Scoring every one of them for each query (exact search) takes well under a millisecond, gives perfect results, and needs no index. So we use exact search inside each tenant.
- A single shared index over all tenants, filtered by tenant afterwards, tends to come back empty, because one tenant is only about 0.07% of it.
- All 621 MiB of vectors can't sit in every pod, because that's more than the 256 MiB allowance.

**Unchecked:** the config only gives totals, so the largest tenant's size is unknown. The repo also doesn't show:
- whether pgvector can be installed
- whether `chunk_vectors` has an index on tenant
- how fast embed-m2 is (every query calls it, so its time comes out of the 150 ms)

I couldn't search the rest of the project for these because search permission was denied. The seven files I read don't mention any of them.

**Live example.** A customer types "can't log in".

| | Average tenant today (160 chunks, about 470 KiB) | Possible Enterprise tenant in Q1 (100,000 chunks, about 293 MiB; Sales hasn't given sizes yet) |
|---|---|---|
| **A. Postgres** | Exact search on the replica. "Resetting your password" comes first. | We add an HNSW index just for this tenant (HNSW is an approximate index: fast on big sets, and it may very rarely miss a match). Results look the same to the customer. |
| **B. In the pods** | Same result. The first search after a pod restarts loads the tenant's vectors first, so that keystroke is a bit slower (not measured). | **Doesn't fit.** 293 MiB is more than the whole 256 MiB allowance, so search for this tenant would be slow or fail until we rebuild it. |

Customers see the same results under both options today. The options only diverge for large tenants.

**Options**

**A. Search inside Postgres with pgvector** (a Postgres extension for vector search). The data team installs it, converts `vec` from raw bytes into a vector column, and adds a tenant index. Queries run on the read replica.
- Pros:
  - Handles Enterprise tenants with per-tenant indexes.
  - The pods stay as they are.
  - There's one copy of the data, with no cache to warm.
- Cons:
  - December depends on a review and a migration that the data team controls.
  - Every keystroke adds load to the replica that the data team's dashboards also read.
  - It's another server round trip inside the 150 ms.

**B. Search inside the API pods; Postgres unchanged.** Each pod loads a tenant's vectors from `chunk_vectors` the first time that tenant searches, and keeps the most recently used tenants in a cache capped under 256 MiB.
- Pros:
  - No dependency on the data team (except possibly a tenant index).
  - Shippable in December.
  - Most searches are answered from memory.
- Cons:
  - Breaks for any tenant above about 250 MiB, which is exactly the Enterprise case, so it would probably need replacing by Q1.
  - Each pod warms its own cache, and that load time isn't measured.

**Recommendation: A if the data team can commit by mid-November, otherwise B for December and then A for Q1. Leaning, not firm.** The deciding fact is the one only you or the data team know: whether pgvector can be ready in time. The strongest case against A is that B ships with nothing outside our control. That doesn't win, because B will fail for Enterprise tenants, so B means building the search twice. It's only worth that if A can't meet December.

**Questions**
1. Can the data team install pgvector, convert `vec`, and add a tenant index on `chunk_vectors` by mid-November? (yes / no / don't know)
2. Do you know the size of the largest tenant today, or of the expected Enterprise tenants? (number / no)
3. Do you know embed-m2's typical response time per query? (ms / no)

---

## Run 3

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 1057 words

# MOSS-311: where should the help-center vector search run?

**Context.** Mossline is a support desk. Each customer company (a "tenant") has its own help center of articles that its customers search. That search currently matches words only, using Postgres full-text search in `search/keyword.py`. A customer who types "can't log in" gets nothing, because the article they need is titled "Resetting your password".

**MOSS-311** is the ticket to make search match meaning. It's due in the December release, about four weeks from now. The groundwork is done. **MOSS-298**, an earlier ticket that's now closed, added a nightly job (`search/embed_corpus.py`). The job cuts every article into 200-word pieces called **chunks**. It sends each chunk to **embed-m2**, the paid embedding service we already use, which returns 768 numbers (a **vector**). Chunks with similar meanings get similar vectors. The job stores the vectors in the `chunk_vectors` table. Nothing reads them yet.

To search, we turn the customer's text into a vector with embed-m2 and find the closest chunks within that tenant. Writing any code waits on one choice: **where that comparison runs.**

**Fixed by the product notes and config:**
- **Latency:** p95 at or under 150 ms (95% of searches finish within 150 ms). Results refresh as the customer types.
- **Isolation:** each tenant sees only its own articles.
- **Size today** (`config/search.yaml`, counted 2026-10-31): 1,340 tenants and 212,000 chunks, so about 160 per tenant on average. That's 621 MiB of vectors in total.
- **Memory:** each of the 4 API pods (the Python servers, `mossline-api`) may use at most 256 MiB more. The platform team agreed this in October. Anything more needs a capacity request, and the next review is in February.
- **Database:** Postgres is run by the **data team**. New extensions and schema changes need their review. The read replica (a read-only copy of the database) also serves their dashboards.
- **Growth:** the Enterprise tier opens in Q1 with "a few large tenants". Their sizes are unknown.

**Settled earlier in this session (my analysis, not yet signed off by you):**
- **Exact search, one tenant at a time.** With about 160 chunks per tenant, comparing the query against every chunk takes microseconds and never misses a result.
- **No single index over all tenants.** An approximate index across everyone mostly returns other tenants' chunks, which then get filtered out, leaving few results.
- **No full copy of all vectors in each pod.** 621 MiB is more than the 256 MiB budget.

**My assumption:** the per-query embed-m2 call takes well under 150 ms. Nothing in the repo says how fast it is.

**What I checked.** The repo has seven files: the ticket, two docs, the config, two Python files and the deploy file. There's no schema or migration. So I couldn't confirm from the project whether pgvector is installed, or whether `chunk_vectors` has an index on `tenant_id`.

**A live example.** A tenant with the average 160 chunks. A customer types "can't log in".

| | A: search in Postgres | B: search in the API pods |
|---|---|---|
| What the customer sees | "Resetting your password" ranked first | Same results |
| Normal search | embed-m2 call + one database query | embed-m2 call + comparison in memory |
| First search for this tenant on a pod (after a restart or after it was dropped from the cache) | No difference | Extra load of about 470 KiB from Postgres before results appear |
| A Q1 Enterprise tenant with, say, 100,000 chunks (≈290 MiB) | An index just for that tenant (HNSW, a kind of fast approximate index), no pod changes | Doesn't fit in the 256 MiB budget. Search slows down or fails until the design is redone |

## Options

**A. Search in Postgres with pgvector** (a Postgres extension that stores vectors and compares them inside the database). The data team installs it, converts the stored vectors to its vector type, and adds an index on `tenant_id`. Searches run on the replica.
- **Pros:**
  - Scales to Enterprise by adding indexes just for the big tenants.
  - No change to pod memory.
  - Data stays fresh with no caching logic.
- **Cons:**
  - December depends on the data team's review and migration, which we don't control.
  - Adds load to the replica that their dashboards also read.

**B. Search in the API pods, Postgres unchanged.** Each pod loads a tenant's vectors the first time that tenant searches. It keeps recently used tenants in a cache capped under 256 MiB and drops the least recently used ones when full.
- **Pros:**
  - Doesn't depend on the data team, except possibly for a `tenant_id` index.
  - Can ship this month.
- **Cons:**
  - One large Enterprise tenant can fill the cache, so this probably needs replacing by Q1. That's two builds.
  - Slower first search per tenant per pod.
  - Cache has to be refreshed after each nightly run.

**C (new): an int8 copy of all vectors in every pod.** Each number is stored in 1 byte instead of 4, about 155 MiB per pod. No cold loads, but there's almost no room for Enterprise, and results are slightly less exact.

## Recommendation

My recommendation hasn't changed: **A if the data team can commit by mid-November, otherwise B for December and then A for Enterprise.** How sure I am: **close call.**

- **The deciding fact:** whether the data team can do it in time. It isn't in the repo and I can't check it.
- **For B:** it's the only option that can certainly ship in December.
- **For A:** it's the design we need by Q1 anyway, and it avoids building twice.
- **What would tip it:** a "yes" from the data team means A. A "no" or no answer means B.

## Questions

1. **Can the data team install pgvector and convert `chunk_vectors` by mid-November?** Answers: yes → A / no → B / don't know → I'll draft the request to them.
2. **Do you know embed-m2's response time for a single query?** A number, or "no".
3. **Has Sales shared any Enterprise help-center sizes yet?** A number, or "no".
4. **Should MOSS-311 also fix a gap in the nightly job?** It never deletes chunks, so removed or shortened articles leave stale chunks behind that search would still return. Yes or no.
