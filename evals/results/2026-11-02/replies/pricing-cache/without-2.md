No problem. Here's the short version.

**Background:** You asked me to add a Redis cache (10-minute TTL) in front of `get_price`, which takes a product SKU and a locale such as `de-DE`. NOTES.md and ticket PRICING-77 both say one thing hasn't been decided yet: what the cache key should be. I haven't changed any files.

**Why it matters:** Most products have a single EUR price that gets converted. A few have special per-country prices, and some of those countries use the same currency. For example, product `B-2210` costs €49 in Germany and €45 in Austria. If the cache stored one entry per product and currency, an Austrian shopper could be shown the German price, or the other way round.

**The question:** Which of these should the cache key be?

1. **Product + full locale** (e.g. `B-2210` + `de-AT`). This always returns the correct price. It stores a few more entries, so it gets slightly fewer cache hits. **This is what I recommend.**
2. **Product + country** (e.g. `B-2210` + `AT`). This shares entries between languages in the same country, so it gets more cache hits. It's only safe if prices never depend on the language. I can't confirm that from the code.

Reply "1" or "2" and I'll implement it.
