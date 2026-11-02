I'm cleaning up dead code in your small Python project in `/work/app`. I've finished looking around, and one file looks dead. I need your OK before I delete it, and nothing else is waiting.

**Context**
- `app/main.py` is the only entry point. It imports `slugify` from `app/utils.py` and prints `slugify('Hello World')`, which gives `hello-world`.
- `app/old_utils.py` is a 3-line file with an older `slugify`. Its first line is a comment: `# superseded by app/utils.py in 2025`. The function only lowercases text; it doesn't turn spaces into `-`.
- When I searched the project, nothing referred to `old_utils`.
- **Decided:** nothing gets deleted without your OK.
- **My assumption:** no code outside `/work` imports `app.old_utils`. My search only covered this folder.
- `/work` isn't under git, so a deleted file can't be restored from history.

**Options**

1. **Delete `app/old_utils.py`**
   - Pros: removes a second `slugify` that behaves differently and could be imported by mistake.
   - Cons: can't be undone here, and anything outside `/work` that imports it would break.
2. **Move it to an archive folder outside `app/`**
   - Pros: can be undone if something outside the folder turns out to need it.
   - Cons: the dead code is still around, just moved, and someone has to remember to clear it out later.
3. **Keep it**
   - Pros: no risk at all.
   - Cons: the leftover duplicate stays in place, which is exactly what this cleanup was meant to remove.

**Recommendation:** Option 1, and I'm fairly sure about it. The file's own comment says it was replaced, nothing here uses it, and it's only 3 lines (all shown above), so even if it were needed again it would be easy to rewrite. The only thing that would change my mind is if you know of code outside `/work` that imports it.

**Should I delete `app/old_utils.py`, move it to an archive folder, or leave it?**
