I need one decision from you before I write the cache: **what to use as the cache key.**

**Context.** Product pages wait about 800 ms for each price from the upstream pricing service. Your team agreed in standup (2026-10-20) to put a Redis cache in front of `get_price`. Prices would be remembered for 10 minutes, so most page loads skip the slow call. Dana owns it, and it has to merge before the Nov 14 sale. The cache key is how the cache tells stored prices apart. Two requests with the same key get the same stored price. Ticket PRICING-77 exists only to pick this key, and it's still open. Nothing is written yet.

`get_price` takes a product code (SKU) and a locale such as `de-DE` (language-country). We ship 40 locales. Most products have one EUR price that upstream converts to local currency. A few products have a separate price per country, set by merchandising:

| Product | Germany (DE) | Austria (AT) | France (FR) | Belgium (BE) |
|---|---|---|---|---|
| B-2210 | €49.00 | €45.00 | | |
| K-0915 | | | €129.00 | €119.00 |

Germany and Austria both use euros but have different prices, and so do France and Belgium. A key of product + currency would therefore be wrong. Whichever country loaded first would set the price shown to the other for up to 10 minutes. Ticket PRICING-81 adds per-country prices for 12 more products in Q1, so this case will grow.

**My assumption:** prices may be up to 10 minutes out of date after the daily exchange-rate update. I'm treating that as accepted when the team chose the 10-minute lifetime.

**Options**

**A. Product + full locale** (e.g. `B-2210` + `de-AT`)
- Pros: The key holds exactly what `get_price` is asked for, so it can't return another locale's price.
- Pros: It stays correct whatever upstream starts varying prices by.
- Cons: Each product can take up to 40 cache entries. If two locales share a country (say `de-CH` and `fr-CH`), each one makes its own slow first call.

**B. Product + country only** (e.g. `B-2210` + `AT`, taken from `de-AT`)
- Pros: Locales in the same country share one entry, so there are fewer slow first calls.
- Cons: It's correct only if upstream prices never depend on the language part of the locale. Nothing in the code confirms that. If that's wrong, customers would see another locale's price.

**Recommendation: A, firmly.** In the locales I can see (`de-DE`, `de-AT`, `fr-FR`, `fr-BE`, `it-IT`, `es-ES`, `nl-NL`, `pl-PL`), every country has exactly one locale. So B saves nothing over A there, and only adds the risk of wrong prices. `locales.txt` lists only those 8 of the 40, so I couldn't check the rest. If many countries have several locales, B would get more of the benefit, but it would still need confirmation that language never affects price.

**Which cache key should I use: A (product + locale) or B (product + country)?**
