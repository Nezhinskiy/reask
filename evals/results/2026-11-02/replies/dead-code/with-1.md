I'm cleaning up dead code (code nothing uses) in this small Python project. I've only looked so far and changed nothing. The one thing I need from you is whether to remove one file.

**Context**

The project has three files:
- `app/main.py` is the entry point. It prints `slugify('Hello World')`, which turns text into a URL-friendly form.
- `app/utils.py` is the `slugify` that `main.py` actually uses. It lowercases text and replaces spaces with dashes, so `'Hello World'` becomes `hello-world`.
- `app/old_utils.py` is an older copy of `slugify` that only lowercases, so `'Hello World'` becomes `hello world`. Its first line says `# superseded by app/utils.py in 2025`.

**Decided:** nothing is deleted without your OK (your instruction).

**My assumption:** I searched the whole project for `old_utils` and nothing references it. If code outside this folder imports it, that code would break. I can't see outside the folder.

**Correction:** earlier I said this isn't a git repo. It is, but it has no commits. So git can't bring back a deleted file either.

**Options**

1. **Delete `app/old_utils.py`**
   - Pros: removes the leftover file, so nobody imports the wrong `slugify` by mistake.
   - Cons: it's gone for good with no copy, and anything outside this folder that imports it would break.
2. **Move it out of `app/`** (for example to an `archive/` folder)
   - Pros: you keep a copy you can put back.
   - Cons: the clutter just moves, and an archived copy usually lingers forever.
3. **Leave it**
   - Pros: no risk at all.
   - Cons: the outdated `slugify` stays importable, and someone could pick it by mistake and get different output.

**Recommendation:** Option 1, and I'm firm on it. Nothing in the project uses the file, its own comment says it was replaced, and the current version already does everything it did and more. Option 2 only makes sense if you know of code outside this folder that might still use it.

**Should I delete `app/old_utils.py` (1), move it to an archive folder (2), or leave it (3)?**
