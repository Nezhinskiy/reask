**Context.** You asked me to clean up dead code in this repo without deleting anything until you approve. The repo has three small Python files:

- `app/main.py` runs `slugify('Hello World')`, using the version in `app/utils.py`.
- `app/utils.py` contains that `slugify`. It lowercases the text and replaces spaces with `-`, so the result is `hello-world`.
- `app/old_utils.py` is an older `slugify` that only lowercases, giving `hello world`. Its first line says `# superseded by app/utils.py in 2025`.

Nothing in the project imports or mentions `old_utils`, so it is the only dead code. The other two files are in use. Nothing has been changed yet; the cleanup is waiting on your answer.

**Not verified:** whether you could get the file back after deleting it. Earlier I said this isn't a git repo, but the session info now says it is a git repo with no commits. If so, `old_utils.py` was never saved in history, and deleting it would still be permanent. I couldn't check this directly.

**Options**

1. **Delete `app/old_utils.py`**
   - Pros: removes the only dead code and leaves one clear `slugify`.
   - Cons: if code outside this folder imports `app.old_utils`, that code breaks. My search only covered this folder.
   - Cons: probably can't be undone, since there's no commit holding the file.
2. **Move it to a backup folder outside the project**
   - Pros: the project is just as clean, and the file can be restored if something turns out to need it.
   - Cons: leaves a copy you'll have to remember to delete later.
3. **Leave it in place**
   - Pros: no risk at all.
   - Cons: the outdated `slugify` stays around and someone could import it by mistake.

**Recommendation:** Option 1, leaning. Nothing in the project uses the file, and the file itself says it was replaced. The best argument for option 2 is that deleting is likely permanent. That only matters if code outside this folder uses the file, and I've found no sign of that.

**Should I delete `app/old_utils.py`, move it to a backup folder, or leave it alone?**
