**Context.** We're adding a Redis cache in front of `get_price` (`pricing/service.py`). Product pages currently wait about 800 ms on each call to the upstream pricing API. Nothing has been written yet. The one thing blocking the work is **what the cache key should be**, so each cached price is reused only for requests that should get exactly that price. PRICING-77 is the ticket for that decision, and it's still open.

**Decided:** Redis, a 10-minute TTL, sitting in front of `get_price`, owned by Dana, merging before the Nov 14 sale (standup, 2026-10-20).
**My assumption:** converted prices can be up to 10 minutes stale after the daily exchange-rate update. That comes with the agreed TTL.

`get_price(sku, locale)` receives a product code and a locale such as `de-DE`. We ship 40 locales. Most products have one EUR price that the API converts. A few have **country prices** set by merchandising, and some of those differ between countries that both use EUR. PRICING-81 adds country prices for 12 more products in Q1.

**Live example.** Product `B-2210` costs €49.00 in Germany and €45.00 in Austria. Here's what each key returns:

| Key | de-DE request | de-AT request (after de-DE) |
|---|---|---|
| product + currency | €49.00 | **€49.00, wrong** (served from the de-DE entry) |
| product + locale | €49.00 | €45.00 |
| product + country | €49.00 | €45.00 |

Product + currency is ruled out. The two keys below are both correct here.

**Options**

**A. Product + locale** (e.g. `B-2210:de-AT`)
- Pros: matches the function's own inputs exactly, so it can't serve a wrong price whatever the API does with the locale.
- Cons: two locales for the same country (e.g. `de-CH` and `fr-CH`) each call the API and keep separate copies, so the hit rate is lower.

**B. Product + country** (e.g. `B-2210:AT`)
- Pros: locales that share a country share one entry, so there are fewer API calls.
- Cons: if the API ever prices by language as well as country, it serves wrong prices for up to 10 minutes. The API client is a stub (`raise NotImplementedError`), so nothing in the code shows which it does.

**Recommendation: A, leaning.** A's correctness doesn't depend on anything we haven't verified. The strongest case for B is the better hit rate. That gain only exists for countries with more than one locale, and the 8 locales in `locales.txt` that I can see are all different countries (the file stops at "# ... 40 in total"). I haven't checked the other 32. If several countries have multiple locales **and** you or Dana know prices never vary by language, B becomes worth it.

**Should the cache key be product + locale (A) or product + country (B)?**
