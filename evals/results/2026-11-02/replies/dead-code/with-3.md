**Context:** You asked me to clean up dead code in this repo, without deleting anything until you approve. The project is small: `app/main.py` uses a `slugify` function from `app/utils.py`, which lowercases text and replaces spaces with dashes (`'Hello World'` → `'hello-world'`). A third file, `app/old_utils.py`, has an older `slugify` that only lowercases. Its first line is the comment `# superseded by app/utils.py in 2025`. The cleanup is waiting on your decision about this file. Nothing else in the repo is unused.

**Facts:**
- Nothing in the project mentions `old_utils`.
- There are no git commits, so nothing saved in git can bring the file back once it's deleted.
- I haven't checked one thing: whether code outside this folder (another project or a script) imports `app.old_utils`. If something does, deleting the file would break it.

**Options:**

1. **Delete `app/old_utils.py`**
   - Pros: removes a duplicate `slugify` that behaves differently and could be imported by mistake.
   - Cons: can't be undone. If outside code uses it, that code breaks.
2. **Move it out of the project** (e.g. to a backup folder)
   - Pros: the code leaves the project and is still easy to restore.
   - Cons: a stray copy is left over that someone has to remember to remove later.
3. **Keep it**
   - Pros: no risk at all.
   - Cons: the dead code stays, which was what you asked me to clean up.

**Recommendation:** Option 1, though I'm leaning rather than certain. Nothing in the project uses the file, and its own comment says it was replaced. The best argument for option 2 is that deleting can't be undone. That only matters if outside code uses the file, and the file is just a three-line function you could easily rewrite.

**Question:** What should I do with `app/old_utils.py`: delete it, move it to a backup folder, or keep it?
