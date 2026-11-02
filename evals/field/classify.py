"""Ask a judge model about each use mine.py found: was there a new option, a changed recommendation?

    python3 evals/field/classify.py uses.jsonl classified.jsonl [model]

Each use goes to `claude -p` (default model claude-sonnet-5-5) with the rubric below, from an
empty scratch directory so no project settings load. The judge's "user_pick" is noisy: it often
reads a second /reask or "explain more" as a choice. Check the picks you report by hand.
"""

import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

src, dst = sys.argv[1], sys.argv[2]
MODEL = sys.argv[3] if len(sys.argv) > 3 else "claude-sonnet-5-5"
workdir = tempfile.mkdtemp(prefix="reask-judge-")
rows = [json.loads(line) for line in Path(src).read_text().splitlines()]

RUBRIC = """You are auditing one use of a "re-ask" skill in a coding-agent session. Do not use any
tools. Read the three parts below and answer with ONE JSON object and nothing else.

ORIGINAL = the agent's message that was pending when the user invoked the re-ask.
REASK = what the agent wrote after the re-ask was invoked.
USER_NEXT = the user's next message (may be empty or unrelated).

Keys:
- "decision_pending": true if ORIGINAL asks the user to decide something (choose, approve, pick a value).
- "new_option": true only if REASK offers at least one concrete course of action that ORIGINAL did not
  offer or mention, not a rewording, a sub-detail, or a merge of two options ORIGINAL already listed.
- "new_option_summary": one short line naming the new option, or "".
- "new_option_recommended": true if REASK recommends that new option.
- "recommendation_changed": true if REASK's recommendation differs from ORIGINAL's, or REASK says a check
  changed its mind. false if ORIGINAL had no recommendation and REASK simply adds one.
- "user_pick": one of "new_option", "original_option", "own_answer", "still_confused", "no_answer".
  "new_option" only if USER_NEXT clearly chooses the option REASK newly introduced.
- "user_decided": true if USER_NEXT makes the decision (any option or their own), false if it asks again,
  shows confusion, or changes the subject.

ORIGINAL:
<<<
{q}
>>>

REASK:
<<<
{r}
>>>

USER_NEXT:
<<<
{u}
>>>
"""


def judge(i_row):
    i, row = i_row
    prompt = RUBRIC.format(q=row["question"], r=row["reask"], u=row["user_next"] or "(none)")
    for _ in range(2):
        p = subprocess.run(
            [
                "claude",
                "-p",
                "--setting-sources",
                "project",
                "--model",
                MODEL,
                "--output-format",
                "json",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=600,
            check=False,
        )
        try:
            res = json.loads(p.stdout)
            text = res["result"].strip()
            text = text[text.index("{") : text.rindex("}") + 1]
            v = json.loads(text)
            v["_cost"] = res.get("total_cost_usd")
            return i, v
        except Exception as e:  # noqa: BLE001
            err = f"{e}: {p.stdout[:200]} {p.stderr[:200]}"
    return i, {"_error": err}


results = {}
with ThreadPoolExecutor(6) as ex:
    for i, v in ex.map(judge, enumerate(rows)):
        results[i] = v
        print(i, "ok" if "_error" not in v else v["_error"][:120], flush=True)
with open(dst, "w") as f:
    for i, row in enumerate(rows):
        f.write(
            json.dumps(
                {"file": row["file"], "ts": row["ts"], "how": row["how"], **results[i]},
                ensure_ascii=False,
            )
            + "\n"
        )
print("cost", round(sum(v.get("_cost") or 0 for v in results.values()), 2))
