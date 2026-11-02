# vector-index-unsure, cell B

## Run 1

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 541 words

**Context.** MOSS-311 adds meaning-based search to the help center, so a customer who types "can't log in" finds the article "Resetting your password". The vectors it needs (each article split into chunks, each chunk turned into 768 numbers) are already computed every night and stored in the `chunk_vectors` table in Postgres. The plan isn't finished because it depends on one thing: **where the search runs**. The design and the index choice both follow from that.

**Decided:** each search looks only at one tenant's articles. Every chunk of that tenant gets scored directly, with no approximate index, because a tenant averages about 160 chunks (212,000 chunks / 1,340 tenants) and that takes microseconds. Results must come back in 150 ms or less (p95), because they refresh as the customer types.

**Unchecked fact the choice depends on:** whether the data team, who own Postgres and review every extension and schema change, can make the change below before the December release. The repo can't tell me. Nobody has measured anything either, so all numbers here are arithmetic on `config/search.yaml`.

**Example: one search under each option**

| | A: search in Postgres | B: search in the API servers |
|---|---|---|
| Typical tenant today (~160 chunks) types "can't log in" | Database scores 160 chunks: fast | Server loads ~470 KB once, then scores in memory: fast |
| Large Enterprise tenant in Q1 (say 100,000 chunks ≈ 290 MB) | Add an index for that tenant only: works | Larger than each server's 256 MB extra-memory limit: breaks |

**Options**

**A. Search inside Postgres.** The data team installs pgvector (a Postgres add-on for storing and searching vectors) and converts the stored vectors to its format. Searches run on the read-only copy of the database.
- Pros: handles large Enterprise tenants by adding an index just for them; no extra memory on our servers.
- Cons: December depends on another team's review and migration; the same database copy also serves their dashboards, so search load would compete with them.

**B. Search inside our 4 API servers; Postgres stays as it is.** Each server loads a tenant's vectors when that tenant first searches, and keeps recently used tenants in memory, up to 256 MB.
- Pros: doesn't depend on the data team, so December is in our hands.
- Cons: one large Enterprise tenant won't fit in 256 MB, and more memory can't be approved before February, so this likely has to be replaced in Q1.

**C. Build B for December and move to A in Q1.**
- Pros: December doesn't depend on the data team, and the Enterprise problem still gets solved.
- Cons: we build search twice.

**Recommendation: A if the data team can commit by mid-November, otherwise C. I'm leaning, not firm.** The strongest case for B alone is that Enterprise tenant sizes are still unknown, so the Q1 problem might never happen. It doesn't win because if one large tenant arrives, B fails with no fix until February.

**The question:** Can the data team install pgvector and convert the vectors before December?
- **Yes** → plan A
- **No, or not sure** → plan C (B now, A in Q1)
- **I'll ask them first** → I'll wait for their answer

---

## Run 2

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick PASS, references PASS; 519 words

**Context.** MOSS-311 is the ticket to make help-center search match what customers mean. Today, typing "can't log in" finds nothing because the right article is titled "Resetting your password". A nightly job already turns every article into vectors (lists of numbers that capture meaning) and stores them in a Postgres table, `chunk_vectors`. Nothing reads them yet. The remaining choice is where the search over those vectors runs, and the plan is waiting on it.

**Decided:**
- Each customer's search only looks at their own company's articles.
- That's about 160 article pieces per company on average, so we can compare against every piece directly. No special search index is needed for December.
- A full copy of all vectors (621 MiB) can't live in each API server. The agreed limit is 256 MiB extra per server, and the next chance to raise it is February.

**My assumption:** the few large Enterprise customers arriving in Q1 may each have far more than 160 pieces. Nobody has given sizes yet.

**What the two options look like in practice**

| | December, average company (~160 pieces) | Q1, a large Enterprise company (sizes unknown) |
|---|---|---|
| **A. Search inside Postgres** | Works, if the data team has made their change in time | Scales: we add a search index just for that company |
| **B. Search inside our API servers** | Works with no help from the data team | One big company could crowd everyone else out of the 256 MiB, so this likely needs replacing |

**Options**

**A. Search inside Postgres.** The data team installs pgvector (a Postgres add-on for vector search) and converts the stored vectors to its format.
- Pros: holds up best when big Enterprise customers arrive; our servers don't change.
- Cons: December depends on a review and migration the data team controls. Postgres extensions and schema changes need their approval. Search load would also share the database copy their reporting dashboards read from.

**B. Search inside our API servers.** Each server loads a company's vectors the first time that company searches, keeps recently used ones in memory under 256 MiB, and compares them there.
- Pros: no dependency on the data team. Loading can probably go through the existing article index, though I can't confirm that from the repo.
- Cons: probably needs rebuilding as option A by Q1. The first search per company per server is slower. A large Enterprise company might not fit at all.

**Recommendation:** leaning A, but only if the data team can commit to finishing by mid-November. If they can't, use B for December and move to A before Enterprise launches. The strongest case for B is that it's the only option guaranteed to ship in December. That's why it's the fallback rather than the plan. What decides it is the data team's availability, and I can't tell that from the repo.

**The question:** Do you know if the data team can add pgvector to our Postgres before the December release?
- **Yes:** plan for A.
- **No, or unknown:** plan for B now, then A for Enterprise.

---

## Run 3

all-decisions FAIL, decision-1 FAIL, facts FAIL, no-trap-pick PASS, references PASS; 588 words

## Where should the vector search run?

**Context.** MOSS-311 changes the help-center search box so it finds articles by meaning. A customer who types "can't log in" should find the article "Resetting your password". Each article is already stored as 768-number vectors, one per 200-word chunk, in a Postgres table called `chunk_vectors`. Nothing reads those vectors yet. The search has to return results in 150 ms or less (p95) while the customer types, and it has to ship in the December release. The rest of the plan can't be written until this is decided.

**Already decided:**
- Each search scores every chunk in the customer's own tenant exactly. A tenant averages about 160 chunks, so this is fast and returns perfect results.
- A full copy of all vectors can't sit in each API server's memory. They take 621 MiB. The platform team allows 256 MiB extra per server, and the next chance to ask for more is February.

**My assumption:** the Enterprise tenants arriving in Q1 may be much bigger than today's. Nobody has given sizes yet.

**What it comes down to:** can the data team, who run Postgres and must approve any change to it, make the change below in time for December? The repo can't tell me that.

**Example: a customer types "can't log in"**

| | A: search inside Postgres | B: search inside our API servers |
|---|---|---|
| Typical tenant today (~160 chunks) | Fast, correct results | Fast, correct results |
| Large Enterprise tenant in Q1 (say 100k chunks, about 290 MiB) | Handled by adding an index for that tenant alone | Larger than the 256 MiB memory allowance, so it can't be cached |
| What December depends on | The data team's review and migration | Only us |

**Options**

**A. Search inside Postgres.** The data team installs pgvector (a Postgres add-on for searching vectors), converts the stored vectors to its format, and adds an index on tenant. Searches run on the read-only copy of the database.
- Pros: handles large Enterprise tenants without a rewrite. No extra memory on our servers.
- Cons: December depends on a review and migration that someone else controls. The read-only copy also serves the data team's dashboards, so search load would compete with them.

**B. Search inside our API servers. Postgres stays as it is.** Each server loads a tenant's vectors the first time that tenant searches and keeps recently used tenants in a cache capped under 256 MiB.
- Pros: we control the December date. The data team might need to add only a tenant index.
- Cons: one large Enterprise tenant could fill the cache or not fit at all, so this probably needs replacing with A by Q1. That means building search twice.

**Recommendation: A, leaning, as long as the data team commits by mid-November.** The strongest case for B is that the deadline stays in our hands, and December is firm. It still loses because B is likely to be rebuilt within a quarter, and A is the only option that handles the Enterprise tenants. If the data team can't commit by mid-November, go with B for December and move to A afterwards.

**The question:** Can the data team install pgvector and convert the vectors before the December release?
- **Yes** → plan A
- **No, or not reliably** → plan B now, A later
- **Don't know** → ask the data team first. That's one message to them, and the plan waits until they reply.
