I'm tidying dead code in your project (the `/work/app` folder). Nothing has been deleted. One decision is left before I make any change.

**Context**
The project has three Python files:
- `app/main.py` is the entry point. It runs `slugify('Hello World')` from `app/utils.py`.
- `app/utils.py` has the current `slugify`, which lowercases text and turns spaces into dashes: `"Hello World"` → `"hello-world"`.
- `app/old_utils.py` has an older `slugify` that only lowercases: `"Hello World"` → `"hello world"`. Its first line reads `# superseded by app/utils.py in 2025`.

Nothing in `/work` mentions `old_utils`, so nothing in this project uses it. There's no `.git` folder in `/work`, so a deleted file can't be brought back from version control. **My assumption:** no code outside `/work` imports `app.old_utils`. I didn't check this.

**Options**
- **A. Delete `app/old_utils.py`**
  - Pros: removes the duplicate `slugify`, so nobody imports the wrong one by mistake.
  - Cons: can't be undone. Anything outside `/work` that imports it will crash.
- **B. Move it to a folder outside `app/`, e.g. `/work/archive/`**
  - Pros: it can't be imported anymore, but you keep a copy.
  - Cons: the dead code still sits in the repo, and an archive folder tends to get forgotten.
- **C. Leave it as is**
  - Pros: no risk.
  - Cons: two different `slugify` functions stay side by side.

**Recommendation:** A, leaning toward it. Nothing in the project uses the file, and its own comment says it was replaced. The strongest argument for B is that the delete can't be undone. It doesn't win because the file is two lines and its logic is just `s.lower()`. If you know of code outside `/work` that imports `app.old_utils`, pick B instead.

**Should I delete `app/old_utils.py` (A), move it to `/work/archive/` (B), or leave it (C)?**
