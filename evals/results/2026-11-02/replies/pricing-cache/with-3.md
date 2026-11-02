**Context.** Product pages wait about 800 ms on each call to the upstream pricing API (`pricing_api.get_price(sku, locale)`). On 2026-10-20 the standup agreed to put a Redis cache with a 10-minute TTL in front of it. Dana owns the work, and it must merge before the Nov 14 sale. The code is small: `pricing/service.py` passes `sku` and `locale` (for example `"de-DE"`) straight to the API, and we ship 40 locales. Ticket PRICING-77, "decide the cache key", is blocked on design. That's the decision I need from you, and nothing gets written until you make it.

What makes the key matter: most SKUs have one EUR list price that the API converts into the local currency. Some SKUs instead have a **country price** set by merchandising, and two countries with the same currency can have different prices. Three SKUs have one today, and PRICING-81 adds 12 more in Q1.

**Decided:** Redis, 10-minute TTL, in front of `get_price`.
**My assumption:** after the daily exchange-rate update, prices may be up to 10 minutes stale. I'm assuming the standup accepted that along with the TTL.

**Live example.** SKU `B-2210` has country prices DE €49.00 and AT €45.00:

| Request | Correct price | Key: SKU + currency | Key: SKU + country | Key: SKU + locale |
|---|---|---|---|---|
| `de-DE` (first) | €49.00 | €49.00, cached | €49.00 | €49.00 |
| `de-AT` (next) | €45.00 | **€49.00, wrong** | €45.00 | €45.00 |

So SKU + currency is out. Two options are left.

**Options**

**A. SKU + locale** (e.g. `B-2210:de-AT`)
- Pros: the key is exactly what the API receives, so the cache can't return a price the API wouldn't have returned.
- Pros: nobody needs to know how the API sets prices.
- Cons: up to 40 entries per SKU. Each locale warms up separately, so the hit rate is lower in the first minutes after each expiry.

**B. SKU + country** (e.g. `B-2210:AT`, with the country taken from the end of the locale)
- Pros: locales that share a country, such as `fr-BE` and a possible `nl-BE`, share one entry, which gives more hits.
- Cons: if the API ever uses the language part of the locale for pricing, two locales silently get each other's price. Nothing in the repo can confirm it doesn't, because the API client is a stub.

**Recommendation: A, leaning.** The strongest case for B is the hit rate during the sale. But the hit-rate gain only happens when two shipped locales share a country. None of the 8 locales in `locales.txt` do (the other 32 aren't listed), so B probably buys little and adds a correctness risk nobody can verify. I'd switch to B if the full locale list has many countries with several languages and someone who knows the API confirms that price depends on country only.

**Should the cache key be SKU + locale (A, recommended) or SKU + country (B)?**
