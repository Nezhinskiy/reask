Sure, here's the short version.

**The problem:** `orders` is big (about 40M rows) and busy. If one migration fills in `region` for every old order at once, it will take longer than the 10-minute deploy limit, and it could freeze writes like the `payments` incident did (INC-212).

**My plan:** do it in small safe steps instead of one big one.
1. Add an empty `region` column. This is instant.
2. Have new orders fill in `region` when they're created.
3. Fill in old orders a little at a time with a separate script, not during deploy.
4. Once every row has a value, make the column required (NOT NULL).

**Three questions for you:**
1. **What are the region values?** The code mentions a `REGIONS` mapping from country to region, but it doesn't exist in the repo. Where is it, and what should happen if a country isn't in it?
2. **Is the current country OK for old orders?** If a customer moved, their old orders would get their *new* country's region. Is that fine for the tax report?
3. **Is the step-by-step plan OK?** That includes running a separate script outside the deploy to fill in old orders.
