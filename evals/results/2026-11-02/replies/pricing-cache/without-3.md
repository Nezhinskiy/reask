Sorry, here it is more simply.

**The question:** When we save a price in the cache, what do we label it with so we can find it again?

**The problem with labeling by product + currency:** Some products cost different amounts in different countries, even when those countries use the same currency. For example, product B-2210 is €49 in Germany and €45 in Austria. If the label were just "B-2210 + EUR", a German shopper could load the page first, and then Austrian shoppers would see €49 for the next 10 minutes. That price is wrong for them.

**Your two choices:**

- **A. Label by product + locale** (like `B-2210` + `de-AT`). This is always correct, because each country and language gets its own saved price. The downside is that more copies get stored, so the cache helps a bit less. This is what I recommend.
- **B. Label by product + country** (like `B-2210` + `AT`). This stores fewer copies, so it's a little faster. It's only safe if the price never depends on the language. For example, German and French speakers in Switzerland would have to always see the same price. I can't tell from the code whether that's true.

**So: A or B?** If you're not sure, pick A.
