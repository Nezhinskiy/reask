**Context.** Product pages wait about 800 ms each time they call the upstream pricing API for a price. The team agreed on 2026-10-20 to put a Redis cache in front of `get_price` that keeps each price for 10 minutes. Dana owns this, and it has to merge before the Nov 14 sale. The only open point is the cache key, which decides which requests share a stored price. NOTES.md and ticket PRICING-77 both leave it open, and I need it before I can write code.

Most products have one euro price that the API converts into each currency. A few products have a separate price per country, set by merchandising. One of them is B-2210, which costs €49.00 in Germany and €45.00 in Austria. Both countries use euros. Ticket PRICING-81 adds 12 more products like this in Q1. `get_price` receives the product code and a locale such as `de-DE`, which is language plus country. We ship 40 locales.

**Live example:** B-2210, first requested from `de-DE` and then from `de-AT`:

| Cache key | Austria is shown |
|---|---|
| product + currency | €49.00, which is wrong (it reuses Germany's entry) |
| product + locale | €45.00, which is right |
| product + country | €45.00, which is right |

So "product + currency" is out. The question is between the other two.

**Options**

1. **Product + locale** (`B-2210:de-AT`)
   - Pros: It can never show a wrong price, because it uses exactly what the API is asked for.
   - Pros: Nothing about the upstream API needs to be confirmed.
   - Cons: Each locale stores its own copy, so up to 40 entries per product.
2. **Product + country** (`B-2210:AT`)
   - Pros: Locales that share a country (say `de-CH` and `fr-CH`) share one entry, so more requests are served from the cache.
   - Cons: If the API ever varies prices by language, users silently see wrong prices for up to 10 minutes.
   - Cons: The gain may be zero. The 8 locales listed in `locales.txt` all have different countries, and the other 32 aren't listed.

**Recommendation:** option 1, though I'm leaning rather than certain. The best argument for option 2 is the better hit rate. But I can't confirm that the API ignores language (the API client is a stub), and I can't confirm that any two of our locales share a country. So option 2 risks wrong prices for a gain that may not exist. Even with option 1, any repeat request within 10 minutes skips the 800 ms wait.

**Should the cache key be product + locale (option 1) or product + country (option 2)?**
