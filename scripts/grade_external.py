"""Grade messages with a case's own LLM graders, outside the eval harness.

    python -m scripts.grade_external CASES_DIR MESSAGES.jsonl OUT.json [--model M] [--votes 3]

MESSAGES.jsonl has one {"case", "label", "text"} per line: `case` names a folder in CASES_DIR
(rendered by build_evals), `label` says what the message is ("question", "neg-no-trap",
"pos-1", "B-3"...). Every `type: llm` grader of that case judges the message, `--votes` times,
majority wins. Used for what the harness cannot do: grader controls (the recorded question and
deliberately broken or good re-asks), re-judging saved replies with other models, and the
returning-user grader on real re-asks.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

Judge = Callable[[str, str], bool]
WRAP = """You are grading the final message an AI coding agent wrote, against one criterion. Do not
use any tools. Reply with PASS or FAIL on the first line, then one sentence of reason.

CRITERION:
{criterion}

FINAL MESSAGE:
<<<
{message}
>>>
"""


def llm_graders(case: Path) -> dict[str, str]:
    out = {}
    for path in sorted((case / "graders").glob("*.md")):
        m = re.match(r"---\n(.*?)\n---\n?(.*)", path.read_text("utf-8"), re.S)
        if m and re.search(r"^type:\s*llm\s*$", m.group(1), re.M):
            out[path.stem] = m.group(2).strip()
    return out


def claude_judge(model: str) -> Judge:  # pragma: no cover
    workdir = tempfile.mkdtemp(prefix="reask-judge-")
    isolation = (
        ["--bare"] if os.environ.get("ANTHROPIC_API_KEY") else ["--setting-sources", "project"]
    )

    def judge(criterion: str, message: str) -> bool:
        p = subprocess.run(
            ["claude", "-p", "--model", model, "--tools", "", *isolation],
            input=WRAP.format(criterion=criterion, message=message),
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=300,
            check=False,
        )
        return p.stdout.strip().upper().startswith("PASS")

    return judge


def grade(
    cases: Path, rows: list[dict[str, str]], judge: Judge, votes: int = 3, workers: int = 8
) -> list[dict[str, object]]:
    jobs = []
    for i, row in enumerate(rows):
        for name, criterion in llm_graders(cases / row["case"]).items():
            jobs += [(i, name, criterion, row["text"])] * votes
    with ThreadPoolExecutor(workers) as pool:
        verdicts = list(pool.map(lambda j: judge(j[2], j[3]), jobs))
    tally: dict[tuple[int, str], list[bool]] = {}
    for (i, name, _, _), verdict in zip(jobs, verdicts, strict=True):
        tally.setdefault((i, name), []).append(verdict)
    out: list[dict[str, object]] = []
    for i, row in enumerate(rows):
        graders = {n: sum(v) * 2 > len(v) for (j, n), v in tally.items() if j == i}
        out.append({"case": row["case"], "label": row["label"], "graders": graders})
    return out


def main(argv: list[str] | None = None, judge: Judge | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cases", type=Path)
    parser.add_argument("messages", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--model", default="claude-sonnet-5-5")
    parser.add_argument("--votes", type=int, default=3)
    args = parser.parse_args(argv)
    rows = [json.loads(line) for line in args.messages.read_text("utf-8").splitlines() if line]
    missing = sorted({r["case"] for r in rows if not (args.cases / r["case"]).is_dir()})
    if missing:
        print(f"no such case: {', '.join(missing)}", file=sys.stderr)
        return 1
    result = grade(args.cases, rows, judge or claude_judge(args.model), args.votes)
    args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(f"graded {len(rows)} messages into {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
