I'm waiting on one decision before I write any code: **what the cache key should be.**

**Context.** Product pages wait about 800 ms on `pricing_api.get_price`, the call to the upstream pricing API. At standup on 2026-10-20 the team agreed to put a Redis cache with a 10-minute TTL in front of it. Dana owns it, and it has to merge before the Nov 14 sale. The one point left open was the cache key, which is ticket PRICING-77 ("Decide cache key for pricing cache, blocked on design"). Nothing has been changed yet.

The function being cached is `get_price(sku, locale)` in `pricing/service.py`. A locale is a language plus a country, like `de-DE` or `de-AT`, and we ship 40 of them.

**Decided:** Redis, 10-minute TTL, cache in front of `get_price`.
**My assumption:** prices up to 10 minutes stale are acceptable, including right after the daily currency-rate update. I take that as part of agreeing to the TTL.

**Why the key matters.** Most products have one EUR price that the API converts to the local currency. Some products instead have a fixed price per country, set by merchandising, and two of those countries can share a currency. If the key leaves out the country, the first country to fill the cache sets the price every other country sees:

| Product | Locale | Correct price | Key = product + currency | Key = product + locale |
|---|---|---|---|---|
| B-2210 | de-DE | €49.00 | €49.00 (fills the cache) | €49.00 |
| B-2210 | de-AT | €45.00 | **€49.00, wrong** | €45.00 |

Today 3 products have country prices: B-2210 (Germany/Austria), K-0915 (France/Belgium) and T-3302 (Italy/Spain). Ticket PRICING-81 adds 12 more in Q1. So product + currency is out. That leaves two options:

**Options**

**A. Key = product + full locale** (e.g. `B-2210:de-AT`)
- Pros: Can't return a wrong price, because it's exactly what the upstream API is asked for.
- Pros: Stays correct whatever merchandising adds later, including PRICING-81.
- Cons: Each locale fills its own cache entries, so the hit rate is lower than if locales shared entries.

**B. Key = product + country only** (e.g. `B-2210:AT`, with `de-CH` and `fr-CH` sharing one entry)
- Pros: Better hit rate, but only if some country has more than one locale.
- Cons: Correct only if the upstream API never prices by language. The code doesn't show that, so a wrong guess means silently wrong prices during the sale.

**Recommendation: A, firmly.** B only helps if some country ships in two languages. Of the 40 locales, `locales.txt` lists only 8 (de-DE, de-AT, fr-FR, fr-BE, it-IT, es-ES, nl-NL, pl-PL), each a different country. So B's gain may be zero, and its risk is wrong prices. If the full list has countries with two or more locales and you know the API ignores language, B is worth reconsidering.

**Should the cache key be product + full locale (A) or product + country (B)?**
