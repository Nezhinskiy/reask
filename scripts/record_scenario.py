"""Record a v2 scenario's pending question: run its steps in a skill-free Claude Code session.

    python -m scripts.record_scenario NAME [--attempts 3] [--out DIR]

Each attempt copies the scenario's project/ into a fresh scratch directory outside the
repository and sends the [record] steps to `claude -p`, one user turn each, resuming the same
session; a `command` step (such as /compact) is sent as that turn. Tools are read-only. With
ANTHROPIC_API_KEY set the session runs under --bare (no CLAUDE.md, hooks, plugins, memory);
without it, user settings, MCP servers and skills are switched off instead.

Every attempt is kept under OUT/NAME/<n>/: the raw session, the final assistant message
(final.md) to judge against the scenario's select rule, and the scratch path to pass to
sanitize_history. Nothing is written inside the repository.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scripts import build_evals

MODEL = "claude-opus-5-5"
TOOLS = ["Read", "Glob", "Grep"]
Runner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]


def isolation(env: dict[str, str]) -> list[str]:
    if env.get("ANTHROPIC_API_KEY"):
        return ["--bare"]
    return ["--setting-sources", "project", "--strict-mcp-config", "--disable-slash-commands"]


def command(step: dict[str, Any], session: str, first: bool, env: dict[str, str]) -> list[str]:
    turn = step.get("prompt") or step["command"]
    resume = ["--session-id", session] if first else ["--resume", session]
    return [
        "claude",
        "-p",
        turn,
        *resume,
        "--model",
        MODEL,
        "--tools",
        *TOOLS,
        "--output-format",
        "json",
        *isolation(env),
    ]


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:  # pragma: no cover
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=1800, check=False)


def session_file(config_dir: Path, scratch: Path, session: str) -> Path:
    """Where Claude Code keeps a session: projects/<cwd with separators as dashes>/<id>.jsonl."""
    slug = re.sub(r"[^A-Za-z0-9-]", "-", str(scratch.resolve()))
    return config_dir / "projects" / slug / f"{session}.jsonl"


def final_message(session_jsonl: str) -> str:
    text = ""
    for line in session_jsonl.splitlines():
        row = json.loads(line) if line.strip() else {}
        if row.get("type") == "assistant" and not row.get("isSidechain"):
            parts = [
                b.get("text", "")
                for b in row["message"].get("content", [])
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            text = "\n".join(p for p in parts if p) or text
    return text


def record(
    scenario: build_evals.Scenario,
    out: Path,
    attempt: int,
    run: Runner = _run,
    env: dict[str, str] | None = None,
) -> Path:
    env = dict(os.environ) if env is None else env
    config_dir = Path(env.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    scratch = Path(tempfile.mkdtemp(prefix=f"reask-rec-{scenario.name}-")) / "project"
    shutil.copytree(scenario.path / "project", scratch)
    session = str(uuid.uuid4())
    dest = out / scenario.name / str(attempt)
    dest.mkdir(parents=True, exist_ok=True)
    log = []
    for i, step in enumerate(scenario.data["record"]["steps"]):
        p = run(command(step, session, i == 0, env), scratch)
        log.append({"step": i, "returncode": p.returncode, "stderr": p.stderr[-2000:]})
        if p.returncode != 0:
            break
    (dest / "log.json").write_text(json.dumps(log, indent=1), "utf-8")
    (dest / "scratch.txt").write_text(str(scratch), "utf-8")
    source = session_file(config_dir, scratch, session)
    if source.is_file():
        shutil.copy(source, dest / "session.jsonl")
        (dest / "final.md").write_text(final_message(source.read_text("utf-8")), "utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path.home() / ".cache" / "reask-record")
    args = parser.parse_args(argv)
    found = [s for s in build_evals.load() if s.name == args.name]
    if not found:
        print(f"no scenario named {args.name}", file=sys.stderr)
        return 1
    for n in range(1, args.attempts + 1):
        dest = record(found[0], args.out, n)
        ok = (dest / "final.md").is_file()
        print(f"{dest}: {'recorded' if ok else 'no session file; see log.json'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
