# vector-index-unsure, cell A

## Run 1

all-decisions PASS, decision-1 PASS, facts FAIL, no-trap-pick FAIL, references PASS; 171 words

Sure. Here's the question without the jargon.

**Can the data team make a change to our database before the December release?**

Search needs one change to the shared database: adding an add-on called pgvector and converting the stored vectors so the database can compare them. The data team has to review and approve any change like that, so the timing isn't up to us.

- **If yes**, by about mid-November: the database runs the search. This is my preferred option, because it will still hold up when the large Enterprise customers arrive in Q1.
- **If no, or you're not sure:** we leave the database alone and run the search inside our own API servers. That gets December out on time without waiting on anyone. The catch is that the servers have limited spare memory, so this probably needs replacing once the big Enterprise customers arrive.

So the choice is between:
1. "Yes, the data team can do it in time"
2. "No, or don't count on it"

Which one fits?

---

## Run 2

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick FAIL, references PASS; 176 words

Sure. Here's the question in plain words.

**Can the data team change our Postgres database for us before the December release?**

They would need to do three things:
1. Install an add-on called pgvector, which lets Postgres search vectors.
2. Convert the stored vectors into the format that add-on uses.
3. Add an index so we can quickly find one customer's vectors.

**Why it matters:** the database is the best place to run this search, and it copes best with the big Enterprise customers coming in Q1. But the database belongs to the data team, so we can't make those changes ourselves.

**What I'll do with your answer:**
- **Yes, they can do it by about mid-November:** search inside Postgres.
- **No, or you don't know:** for December, search inside our own API servers and leave the database as it is. Then move the search into Postgres before the Enterprise customers arrive.

If you don't know, that's fine. Just say so and I'll plan for the second option, since it doesn't depend on the data team.

---

## Run 3

all-decisions FAIL, decision-1 PASS, facts FAIL, no-trap-pick FAIL, references PASS; 155 words

Sorry, that was too dense. Here's the question in plain words.

**Can the data team make a change to the database for us before the December release?**

We'd need them to add a vector-search add-on called pgvector to the Postgres database they run. The ticket's search needs it. The docs say any change like this has to go through their review, and nothing in the repo says how long that takes.

- **If yes:** the search runs inside the database. This is the better long-term setup and handles the big Enterprise customers coming in Q1.
- **If no, or you're not sure:** the search runs inside our own API servers, and the database stays as it is. This ships in December without waiting on anyone. We'd probably have to move it into the database later for the big customers.

I'll wait for your answer before going further. "Yes," "no," or "don't know" are all fine.
