"""Find every real reask use in your Claude Code transcripts: question, re-ask, your next answer.

    python3 evals/field/mine.py ~/.claude/projects uses.jsonl

Reads the session files under the projects directory (subagent transcripts excluded), finds each
time reask ran (a typed /reask, or the agent loading the skill on its own) and writes one JSON
line per use: the agent's pending question, the re-ask, and the user's next message. The same
use copied into several transcripts (a resumed or forked session) is kept once.

The output is your own work and stays on your machine; only tally.py's counts are meant to be
shared.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT, DST = Path(sys.argv[1]).expanduser(), Path(sys.argv[2])
CMD = re.compile(r"<command-name>/reask(?::reask)?</command-name>")
SKILL = re.compile(r'"name":"Skill","input":\{"skill":"(?:reask:)?reask"')
# rows the app writes in the user's role; they are not the person's reply
NOT_HUMAN = re.compile(
    r"\s*<(task-notification|system-reminder|side-sessions-event|ci-monitor-event|local-command|bash-|agent-message)"
)
SKIP = ("-reask-", "-reask/")  # the skill's own repository: tests and benchmark runs, not use
# sessions started in a temp directory are scripted runs (eval harnesses, scratch agents), not a person
TEMP = re.compile(r"^-(private-)?(tmp|var-folders)-")


def blocks(msg):
    c = msg.get("content")
    return [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])


def event(r):
    m = r.get("message") or {}
    if r.get("type") == "user":
        bs = blocks(m)
        if any(b.get("type") == "tool_result" for b in bs):
            out = []
            for b in bs:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    out.append(
                        c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)[:2000]
                    )
            return ("tool_result", "\n".join(out))
        if r.get("isMeta"):
            return ("meta", "")
        text = "\n".join(b.get("text", "") for b in bs if b.get("type") == "text")
        return ("system", text[:300]) if NOT_HUMAN.match(text) else ("user", text)
    if r.get("type") == "assistant":
        text, tools = [], []
        for b in blocks(m):
            if b.get("type") == "text":
                text.append(b["text"])
            elif b.get("type") == "tool_use":
                tools.append((b.get("name"), b.get("input")))
        return ("assistant", ("\n".join(text), tools))
    return None


def loads_reask(e):
    return e[0] == "assistant" and any(
        t == "Skill"
        and isinstance(i, dict)
        and re.fullmatch(r"(reask:)?reask", str(i.get("skill", "")))
        for t, i in e[1][1]
    )


def uses(path):
    ev = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not r.get("isSidechain") and (e := event(r)):
            ev.append((e, r.get("timestamp", "")))
    users = [j for j, (e, _) in enumerate(ev) if e[0] == "user"]
    done = set()
    for i, (e, _) in enumerate(ev):
        if e[0] == "user" and CMD.search(e[1]):
            trig, how = i, "command"
        elif loads_reask(e):
            trig, how = max((j for j in users if j < i), default=None), "auto"
        else:
            continue
        if trig is None or trig in done:
            continue
        done.add(trig)
        prev = max((j for j in users if j < trig), default=-1)
        nxt = min((j for j in users if j > trig), default=len(ev))
        q_text, q_ask = [], []
        for j in range(prev + 1, trig):
            if ev[j][0][0] == "assistant":
                text, tools = ev[j][0][1]
                q_text += [text] if text.strip() else []
                q_ask += [inp for t, inp in tools if t == "AskUserQuestion"]
        r_text, r_ask, answers = [], [], []
        for j in range(trig + 1, nxt):
            kind, val = ev[j][0]
            if kind == "assistant":
                r_text += [val[0]] if val[0].strip() else []
                r_ask += [inp for t, inp in val[1] if t == "AskUserQuestion"]
            elif kind == "tool_result" and r_ask and "answer" in val.lower():
                answers.append(val[:1500])
        question = (q_text[-1] if q_text else "") + (
            "\n\n[AskUserQuestion] " + json.dumps(q_ask, ensure_ascii=False) if q_ask else ""
        )
        reask = "\n\n".join(r_text) + (
            "\n\n[AskUserQuestion] " + json.dumps(r_ask, ensure_ascii=False) if r_ask else ""
        )
        user_next = ev[nxt][0][1][:1500] if nxt < len(ev) else ""
        if answers:
            user_next = ("[answered in the question UI] " + " | ".join(answers) + "\n" + user_next)[
                :2500
            ]
        if question.strip() and reask.strip():
            yield {
                "file": str(path),
                "ts": ev[trig][1],
                "how": how,
                "question": question[:12000],
                "reask": reask[:30000],
                "user_next": user_next,
            }


seen, n = set(), 0
with open(DST, "w") as out:
    for path in sorted(ROOT.rglob("*.jsonl")):
        project = path.relative_to(ROOT).parts[0]
        if "/subagents/" in str(path) or any(s in str(path) for s in SKIP) or TEMP.match(project):
            continue
        raw = path.read_text(errors="replace")
        if not (CMD.search(raw) or SKILL.search(raw)):
            continue
        for u in uses(path):
            key = hashlib.sha1(u["reask"][:2000].encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                out.write(json.dumps(u, ensure_ascii=False) + "\n")
                n += 1
print(n, "uses")
