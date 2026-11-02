No problem. The plan is to cache `get_price` results in Redis for 10 minutes. Before I write it, I need you to decide one thing: **what each cache entry is keyed by.** NOTES.md and ticket PRICING-77 list this as undecided.

**Why it matters:** Most products have a single EUR price. But a few products have different prices in countries that share a currency. For example, `B-2210` costs €49 in Germany and €45 in Austria (`pricing/pricing_api.py:8-12`). If the key only covered product + currency, a German visitor could fill the cache and Austrian visitors would then see €49 for up to 10 minutes.

**The question:** Which key should I use?

- **A. Product + full locale (e.g. `B-2210` + `de-AT`)**: This is my recommendation. It's always correct because the key matches exactly what `get_price` is called with. The downside is a lower cache hit rate, since each of the 40 locales gets its own entry.
- **B. Product + country (e.g. `B-2210` + `AT`)**: This gives a slightly better hit rate. But it's only correct if prices never depend on the language part of the locale, and I can't confirm that from the code.

If you have no strong preference, reply "A" and I'll implement it.
