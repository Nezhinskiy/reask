"""Turn a recorded Claude Code session into a benchmark history.jsonl, and find what must not ship.

    python -m scripts.sanitize_history SESSION.jsonl OUT.jsonl --cwd /path/the/session/ran/in

Keeps only the dialogue rows (user and assistant, main thread), and in them only the keys the
eval harness replays. The recording's working directory becomes /work and any other home path
becomes ~. Text the harness injected (system reminders: CLAUDE.md, memory, MCP instructions) is
dropped. The output is then scanned; any leak left fails the run, and the same scan runs as a
test over every committed history.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROW_KEYS = (
    "parentUuid",
    "isSidechain",
    "isCompactSummary",
    "type",
    "message",
    "uuid",
    "timestamp",
    "sessionId",
    "cwd",
    "userType",
    "version",
    "sourceToolAssistantUUID",
)
MESSAGE_KEYS = ("id", "type", "role", "model", "content", "stop_reason")
REMINDER = re.compile(r"\s*<system-reminder>.*?</system-reminder>\s*", re.S)
LEAKS = {
    "home path": re.compile(r"/(?:Users|home)/(?!\.\.\.)[A-Za-z0-9._-]+"),
    "temp path": re.compile(r"/(?:private/)?(?:tmp|var/folders)/"),
    "e-mail": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.)[A-Za-z0-9-]+\.[A-Za-z.]{2,}\b"),
    "token": re.compile(r"\b(?:sk-ant-|ghp_|gho_|github_pat_|xox[bp]-|AKIA)[A-Za-z0-9_-]{8,}"),
    "system reminder": re.compile(r"<system-reminder>"),
    # Claude Code names a session's folder after its directory, separators turned into dashes.
    "path as a folder name": re.compile(
        r"-(?:Users|home)-[A-Za-z0-9._]+-|-(?:private-)?var-folders-"
    ),
}


def _slug(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "-", path)


def _scrub(value: Any, paths: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        value = REMINDER.sub("\n", value).strip("\n") if "<system-reminder>" in value else value
        for old, new in paths:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_scrub(v, paths) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v, paths) for k, v in value.items()}
    return value


def sanitize(lines: list[str], cwd: str, home: str) -> list[dict[str, Any]]:
    # Longest first, so the working directory wins over the home directory that contains it.
    resolved = str(Path(cwd).resolve())
    # The scratch directory's parent too: an agent that mistypes the path (a dash for a slash)
    # still names the temporary folder the recording ran in.
    parents = {str(Path(cwd).parent), str(Path(resolved).parent)}
    pairs = {(cwd, "/work"), (resolved, "/work"), (home, "~")} | {(p, "/work") for p in parents}
    pairs |= {(_slug(cwd), "-work"), (_slug(resolved), "-work"), (_slug(home), "-home")}
    paths = sorted(pairs, key=lambda p: len(p[0]), reverse=True)
    rows = []
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("type") not in ("user", "assistant") or row.get("isSidechain"):
            continue
        kept = {k: row[k] for k in ROW_KEYS if k in row}
        kept["message"] = {k: row["message"][k] for k in MESSAGE_KEYS if k in row["message"]}
        rows.append(_scrub(kept, paths))
    return rows


def leaks(text: str) -> list[str]:
    return sorted(name for name, pattern in LEAKS.items() if pattern.search(text))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("session", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--cwd", required=True, help="the directory the session was recorded in")
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args(argv)
    rows = sanitize(args.session.read_text("utf-8").splitlines(), args.cwd, args.home)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    found = leaks(text)
    if found:
        print(f"not written, still contains: {', '.join(found)}", file=sys.stderr)
        return 1
    args.out.write_text(text, "utf-8")
    print(f"{len(rows)} rows written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
