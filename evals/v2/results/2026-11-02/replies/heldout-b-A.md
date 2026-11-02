# heldout-b, cell A

## Run 1

all-decisions PASS, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 248 words

Sure. Here it is more simply.

**The problem:** If k-east has trouble tonight, you need to send users back to old-dc within 15 minutes. With tonight's plan (switching the DNS record), some users could stay stuck on k-east for up to 24 hours. That's because the DNS record tells computers to remember the address for a full day.

**I need two answers from you:**

**1. Has anyone shortened that "remember for a day" setting since 30 October?**
In the DNS provider's console, look at the `api.stagelark.example` record and tell me its TTL number.
- If it shows **300 or lower**, and it was changed **before 22:00 last night (Sunday)**, tonight's plan works as written.
- If it still shows **86400**, I need your answer to question 2.

**2. If it's still 86400, which do you want?**
- **Option A: switch tonight a different way (my pick).** Leave the DNS alone. Instead, tell old-dc's load balancer to forward all traffic to k-east. To go back, you tell it to stop forwarding, which takes seconds. The catch is that it's an unplanned config change on the load balancer, and the runbook needs rewriting before 22:00.
- **Option B: don't switch tonight.** Tonight, only shorten the "remember" setting to 5 minutes and get k-east ready. Do the actual switch at least a day later. The catch is that the announced window moves, so the status page needs updating.

What's the TTL number, and if it's 86400, is it A or B?

---

## Run 2

all-decisions PASS, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 243 words

Sure, here it is more simply.

**The problem:** Tonight's plan switches traffic by changing the DNS record. Right now, computers remember that record for 24 hours. So if k-east breaks and you switch back, some users would stay stuck on k-east for up to a day. You need the bungee to work in 15 minutes, so the plan as written can't run tonight.

**Question 1: What does the DNS console show right now?**
Open the DNS provider's console and look at the TTL on the `api` record.
- If it says **300 or lower**, and it was changed before 22:00 yesterday, the current plan is fine as written.
- If it says **86400**, I need your answer to question 2.

**Question 2: Which option do you want?**

- **Option A: Switch tonight, inside old-dc (my recommendation).** Don't touch DNS. Users keep going to old-dc's HAProxy, and HAProxy sends their requests on to k-east. If k-east breaks, you point HAProxy back at the old servers, and that takes seconds. The downside is that it's an unplanned HAProxy change, and the runbook has to be rewritten.
- **Option B: Prepare tonight, switch later.** Tonight you lower the DNS memory time to 5 minutes and check that k-east is ready. You do the DNS switch at least 24 hours later. The downside is that you have to announce a new window on the status page.

Just reply with what the console shows, and **A** or **B**.

---

## Run 3

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 244 words

Sorry, here it is more simply.

**The problem:** the runbook switches traffic by changing DNS. But DNS answers for `api` are saved for 24 hours. If k-east goes wrong and you change the record back, some users stay on k-east for up to a day. That breaks the bungee's 15-minute limit.

**First question: what does the DNS console show right now for `api`?**
Open the DNS provider's console and look at the TTL on the `api` record.
- If it says **300 or less** and was changed before 22:00 yesterday, the runbook works as written, and we can run it tonight.
- If it still says **86400**, I need your answer to the second question.

**Second question (only if it says 86400): which plan do you want?**
- **Plan A: switch tonight using HAProxy, not DNS (my pick).** DNS stays the same. At 22:00 we tell old-dc's HAProxy to send traffic on to k-east. If k-east goes wrong, we point HAProxy back at the old servers, and that takes seconds. The catch: it's a config change nobody has reviewed for tonight, and the runbook needs rewriting.
- **Plan B: only prepare tonight, switch another night.** Tonight we lower the TTL to 300 and get k-east ready, then do the DNS switch at least a day later. The catch: you have to announce a new window on the status page.

So I need two answers: **the TTL number**, and if it's 86400, **A or B**.
