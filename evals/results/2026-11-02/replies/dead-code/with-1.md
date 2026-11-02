I'm cleaning up dead code in this small project, and one file is the only candidate: `app/old_utils.py`. I need your OK before removing it.

**Context**
- The project has three files. `app/main.py` turns "Hello World" into a URL-friendly string (`hello-world`) using the `slugify` function in `app/utils.py`.
- `app/old_utils.py` holds an older `slugify` that only lowercases the text and doesn't replace spaces. Its first line says `# superseded by app/utils.py in 2025`.
- A search of this project found no code that uses `old_utils`. Nothing else here is dead.
- There's no `.git` folder inside this project, so I can't confirm git could restore a deleted file. I also can't see code outside this folder that might import it.

**Options**
1. **Delete it**
   - Pros: removes the confusion of two `slugify` functions that behave differently.
   - Cons: it can't be undone. If outside code imports it, that code breaks.
2. **Move it out of `app/`** (for example to `archive/old_utils.py`)
   - Pros: the code tree is clean and a copy is kept.
   - Cons: it's still clutter, just in a different folder.
3. **Leave it**
   - Pros: no risk.
   - Cons: dead code that behaves differently stays next to the live version.

**Recommendation:** Option 1, though not firmly. Nothing here uses the file, and its own comment says it was replaced. If you know of any code outside this folder that might import it, choose 2.

**Should I delete `app/old_utils.py` (1), move it to an archive folder (2), or leave it (3)?**
