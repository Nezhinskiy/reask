**Context.** Product pages are slow because each one waits about 800 ms for the upstream pricing service. At standup on Oct 20 the team agreed to put a Redis cache in front of `get_price`. Redis is a fast in-memory store, and each saved price would expire after 10 minutes. Dana owns it, and it must merge before the Nov 14 sale. The one thing nobody has settled is the cache key: which parts of a request decide whether we can reuse a saved price. That's ticket PRICING-77, and I can't write the code until it's answered.

**Decided:** Redis, 10-minute expiry, cache in front of `get_price(sku, locale)`. A locale looks like `de-DE`, which is language `de` plus country `DE`. We ship 40 of them.

**What makes this tricky.** Most products have one euro price that gets converted to the local currency. Some have a price set by hand for each country, even between countries that use the same currency:

| Request | Correct price | Key: product + currency | Key: product + locale |
|---|---|---|---|
| B-2210, `de-DE` | €49.00 | €49.00 (saved first) | €49.00 |
| B-2210, `de-AT` | €45.00 | **€49.00 ✗** (reuses Germany's price) | €45.00 ✓ |

So "product + currency" is out. It would show Austrians the German price. There are 3 such products now, and 12 more are planned for Q1 (PRICING-81).

**Options**

1. **Product + locale** (e.g. `B-2210:de-AT`)
   - Pros: it's exactly what we send to the pricing service, so it can never return the wrong price.
   - Cons: every locale fills its own cache entries, so the first visitor per locale per 10 minutes still waits 800 ms.
2. **Product + country** (e.g. `B-2210:AT`)
   - Pros: two locales in the same country (say `fr-BE` and `nl-BE`) would share an entry, so there would be slightly fewer slow requests.
   - Cons: it's only safe if the pricing service never varies the price by language. The service's code is just a placeholder, so I can't confirm that. If it's wrong, customers would see the wrong price.

**Recommendation: option 1. I'm firm on this.** The 8 locales I can see each belong to a different country, so option 2 shares nothing for them and adds risk for no gain. It would only pay off if some of the other 32 locales share a country, and even then only if language never affects the price.

My assumption: after the daily currency-rate update, converted prices can be up to 10 minutes out of date. I'm treating that as accepted along with the 10-minute expiry.

**Should the cache key be product + locale (option 1) or product + country (option 2)?**
