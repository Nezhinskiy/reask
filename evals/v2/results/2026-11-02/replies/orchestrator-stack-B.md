# orchestrator-stack, cell B

## Run 1

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 543 words

**Context.** PR #14 is the last of three stacked PRs for nightjar 2.0. It removes the old `--legacy-paths` option. That option made nightjar read its data from the old folder `~/.nightjar/` instead of the newer `$XDG_DATA_HOME/nightjar`, which has been the default since 1.6. The code change itself is fine: unit tests and lint pass.

The failing check compares the server schedule (a list of timed commands the hosts run every day) against the new code. One of those commands still uses the removed option:

```
06:15 daily:  nightjar send-digest --legacy-paths --since 24h
```

With #14 merged, that command would stop with an error, and the daily sales digest email wouldn't go out.

Two things make this harder than a one-line fix:

- **We can't fix the schedule from our repo.** The copy in `deploy/crontab` is overwritten every night from the ops team's own repository. Only an OPS ticket changes the real schedule, and ops apply those on Wednesdays. The next window is Wed 4 Nov.
- **We don't know which folder the hosts' data is in.** The daily `collect` command runs without the option, so it uses the new folder. `send-digest` runs with it, so it reads the old one. Nothing in this repo shows which folder actually holds the data. Only ops can check that on the hosts.

**Decided:** nothing yet for #14. #13 (what happens on hosts that only have the old `nightjar.ini` file) is still open, and you've parked it. **My assumption:** 2.0 doesn't have a fixed release date.

**What changes for the 06:15 digest:**

| | CI | 06:15 digest after release |
|---|---|---|
| 1. Wait for ops | green after Wed 4 Nov | runs on the folder ops confirmed |
| 2. Keep the option as a harmless leftover | green now | runs, but now reads the new folder. If the data is in the old one, the email goes out empty |
| 3. Ship 2.0 without #14 | #14 stays red | unchanged, still reads the old folder |

**Options**

1. **File an OPS ticket and wait.** Ops remove the option from the schedule and confirm where the data is.
   - Pros: the real fix, and the data question gets answered.
   - Cons: #14, and so the 2.0 tag, waits at least until Wednesday and depends on ops.
2. **Make #14 accept the option and ignore it, with a warning.**
   - Pros: CI goes green today.
   - Cons: the digest could silently send nothing, the same kind of problem as in #13.
3. **Take #14 out of 2.0.**
   - Pros: 2.0 doesn't depend on ops.
   - Cons: removing an option later means a breaking change in a minor release (2.x), and a major release like 2.0 is the normal place for that.

**Recommendation:** option 1, leaning. The strongest case is for option 3, because it doesn't wait on ops. But 2.0 is already waiting on your #13 decision, so the few days until Wednesday cost almost nothing. Option 1 also keeps the breaking change in 2.0. If 2.0 has a deadline before Wednesday, I'd switch to option 3.

**Should we file the OPS ticket and wait (1), make #14 ignore the old option for now (2), or leave #14 out of 2.0 (3)?**

---

## Run 2

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 434 words

I'll take it again from the start. You put the #13 question aside, so this one is only about #14.

**Context.** Nightjar 2.0 is three pull requests (PRs) stacked on each other. The plan in STACK.md is to tag 2.0 only after all three are merged. #14, the last one, removes the old `--legacy-paths` option. That option tells nightjar to read its data from the old folder `~/.nightjar/` instead of the newer standard folder `$XDG_DATA_HOME/nightjar`. #14's code and unit tests are fine. One automated check fails: it tests every scheduled job against the new code. One real job still uses the removed option:

`06:15 every day: nightjar send-digest --legacy-paths --since 24h` (this emails the daily digest to the sales team)

With #14 merged, that job would fail with "unrecognized arguments" and the digest would stop going out.

We can't fix this by editing the schedule in our repo. The real schedule belongs to the ops team, in their own repository. Our copy gets overwritten every night, so an edit here wouldn't survive. Ops only make changes through a ticket, and they apply them on Wednesdays. The earliest would be Wed 4 Nov.

**Assumption I haven't checked:** where the data actually lives on the servers. The #14 report says it's all in the new folder. But the digest job still reads the old one, while the `collect` job, which gathers the data, writes to the new one. Only ops can confirm this, from the servers.

**Options**

1. **Ask ops to remove the option from the schedule, then wait.**
   Pros: #14 stays clean; the 2.0 plan is unchanged; ops confirm the data folder as part of the change.
   Cons: 2.0 waits until at least Wednesday, longer if ops miss this week's window.
2. **Make #14 accept the option but ignore it, with a warning.**
   Pros: the check passes today.
   Cons: the digest quietly switches folders. If the data really is in the old folder, sales get empty digests and nothing reports an error.
3. **Take #14 out of 2.0.** Release with #12 and #13 only, and add #14 later.
   Pros: 2.0 doesn't wait for ops.
   Cons: changes the agreed plan, and the removal slips to a later release.

**Recommendation: option 1, leaning.** The best argument for option 3 is speed. But 2.0 can't ship today anyway, because #13 is waiting on your decision. So waiting until Wednesday costs little. I'd rule out option 2 until we know where the data is.

**For #14, which do you want: 1 (ticket to ops, then wait), 2 (accept and ignore the option), or 3 (leave #14 out of 2.0)?**

---

## Run 3

all-decisions FAIL, decision-1 FAIL, decision-2 FAIL, facts FAIL, no-trap-pick PASS, references FAIL; 496 words

You're deciding how to get PR #14 back to passing checks. (The #13 question about hosts that still only have `nightjar.ini` is parked, as you asked.)

**Context**

PR #14 is the last of the three PRs for nightjar 2.0. It removes the `--legacy-paths` option. That option made nightjar read its data from the old folder `~/.nightjar/` instead of the current one, `$XDG_DATA_HOME/nightjar`. The plan is to tag 2.0 once all three PRs are merged.

The unit tests and lint pass. One check fails: `deploy-smoke`, which tries every scheduled job in `deploy/crontab` against the new code. One of those jobs still uses the removed option:

```
15 6 * * *   nightjar send-digest --legacy-paths --since 24h
```

That job sends the sales team their digest every day at 06:15. After #14 it would stop with "unrecognized arguments".

We can't fix that line in this repo. `deploy/crontab` is only a copy of a file the ops team owns. A sync overwrites the copy every night at 02:00 UTC, and the servers run the ops version. To change it, you file a ticket with ops, and they apply changes on Wednesdays. The earliest is Wed 4 Nov, then CI passes after the sync that night.

**Assumptions (mine, not checked):** the session that wrote #14 says every server keeps its data in the new folder. But this daily job still points at the old folder, so it may be reading data from there. I can't look at the servers from here. Ops should confirm where the data is before the option goes away, whichever option you pick.

**Options**

1. **Ask ops to remove the option from the schedule, and wait.**
   - Pros: removing an option breaks things for anyone who still uses it. A major release like 2.0 is where that belongs. Also, #14 needs no changes.
   - Cons: 2.0 can't be tagged before Thu 5 Nov at the earliest, and only if ops acts that Wednesday.
2. **Keep `--legacy-paths` as an option that does nothing and prints a warning.**
   - Pros: checks pass today.
   - Cons: the 06:15 job would quietly switch folders. If the data is really in the old one, the sales team gets an empty or wrong digest with no error.
3. **Take #14 out of 2.0.** Ship 2.0 with #12 and #13, and merge #14 later.
   - Pros: 2.0 doesn't depend on ops.
   - Cons: removing the option later breaks things in a minor release like 2.1, where users don't expect it. You still need the ops ticket either way.

**Recommendation:** option 1, but I'm leaning, not certain. The strongest case against it is that it makes 2.0 depend on ops. But 2.0 is also waiting on your #13 answer, and removing an option belongs in a major release. If 2.0 has a fixed date before Thursday, go with option 3.

**Question:** for #14, do you want 1 (ticket for ops, then wait), 2 (option that does nothing), or 3 (leave it out of 2.0)?
