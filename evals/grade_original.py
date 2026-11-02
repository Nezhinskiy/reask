"""Grade each case's ORIGINAL pending question with the case's own rubric files, 3 judge votes each.

This is the "answer without re-asking" column: what the user had in front of them before any
re-ask. Graders that only make sense for a re-ask (new-option, keeps-answers, skill-fired) are
skipped. The judge sees the same rubric text the eval harness uses, with its own short wrapper.

    python3 evals/grade_original.py evals evals/results/<date>/original-question.json
"""

import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVALS, OUT = Path(sys.argv[1]), Path(sys.argv[2])
WORK = Path(tempfile.mkdtemp(prefix="reask-judge-"))
SKIP = {"new-option", "keeps-answers", "skill-fired"}

WRAP = """You are grading the final message an AI coding agent wrote, against one criterion. Do not
use any tools. Reply with PASS or FAIL on the first line, then one sentence of reason.

CRITERION:
{criterion}

FINAL MESSAGE:
<<<
{message}
>>>
"""


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    meta = dict(re.findall(r"^(\w+):\s*'?(.*?)'?$", m.group(1), re.MULTILINE))
    return meta, m.group(2).strip()


def vote(args):
    criterion, message = args
    p = subprocess.run(
        ["claude", "-p", "--setting-sources", "project", "--model", "claude-sonnet-5-5"],
        input=WRAP.format(criterion=criterion, message=message),
        capture_output=True,
        text=True,
        cwd=WORK,
        timeout=300,
        check=False,
    )
    return p.stdout.strip().upper().startswith("PASS")


jobs, keys = [], []


def question(case):
    """The agent's last text in the replayed history: the pending question."""
    text = ""
    for line in (case / "history.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["type"] == "assistant":
            parts = [b["text"] for b in row["message"]["content"] if b.get("type") == "text"]
            text = "\n".join(parts) or text
    return text


cases = sorted(p for p in EVALS.iterdir() if (p / "case.yaml").exists())
for case in cases:
    message = question(case)
    for g in sorted((case / "graders").glob("*.md")):
        if g.stem in SKIP:
            continue
        meta, body = frontmatter(g.read_text())
        if meta["type"] == "regex":
            words = len(message.split())
            keys.append((case.name, g.stem, "regex", words <= 200))
            continue
        for _ in range(3):
            jobs.append((body, message))
            keys.append((case.name, g.stem, "vote", None))

with ThreadPoolExecutor(6) as ex:
    votes = iter(ex.map(vote, jobs))
    res = {}
    for case, grader, kind, val in keys:
        v = val if kind == "regex" else next(votes)
        res.setdefault(case, {}).setdefault(grader, []).append(v)

summary = {
    c: {g: (sum(v) >= 2 if len(v) == 3 else v[0]) for g, v in gs.items()} for c, gs in res.items()
}
for case in cases:
    summary[case.name]["_words"] = len(question(case).split())
OUT.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=1))
