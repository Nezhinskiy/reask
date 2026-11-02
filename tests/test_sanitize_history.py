import json
from pathlib import Path

import pytest

from scripts import sanitize_history

ROOT = Path(__file__).resolve().parent.parent
CWD = "/Users/alice/scratch/run-1"
HOME = "/Users/alice"


def _row(**fields: object) -> str:
    return json.dumps(fields)


SESSION = [
    _row(type="summary", summary="not dialogue"),
    _row(
        type="user",
        uuid="u1",
        cwd=CWD,
        gitBranch="main",
        message={
            "role": "user",
            "content": "<system-reminder>\nCLAUDE.md: be terse\n</system-reminder>\nRead "
            f"{CWD}/NOTES.md and {HOME}/.claude/settings.json",
        },
    ),
    _row(type="assistant", isSidechain=True, message={"role": "assistant", "content": "sub"}),
    "",
    _row(
        type="assistant",
        uuid="a1",
        isCompactSummary=True,
        message={
            "role": "assistant",
            "model": "claude-opus-5-5",
            "usage": {"input_tokens": 3},
            "content": [{"type": "text", "text": f"Done in {CWD}."}],
        },
    ),
]


def test_keeps_the_dialogue_and_only_the_replayed_keys() -> None:
    rows = sanitize_history.sanitize(SESSION, CWD, HOME)
    assert [r["uuid"] for r in rows] == ["u1", "a1"]
    assert "gitBranch" not in rows[0]
    assert rows[0]["cwd"] == "/work"
    assert rows[1]["isCompactSummary"] is True
    assert "usage" not in rows[1]["message"]
    assert rows[1]["message"]["content"] == [{"type": "text", "text": "Done in /work."}]


def test_paths_and_reminders_are_scrubbed() -> None:
    [user, _] = sanitize_history.sanitize(SESSION, CWD, HOME)
    assert user["message"]["content"] == "Read /work/NOTES.md and ~/.claude/settings.json"


@pytest.mark.parametrize(
    ("text", "leak"),
    [
        ("see /Users/bob/notes", "home path"),
        ("see /home/bob/notes", "home path"),
        ("wrote /private/tmp/x", "temp path"),
        ("mail bob.smith@corp.io", "e-mail"),
        ("key sk-ant-abcdefgh12345", "token"),
        ("<system-reminder>", "system reminder"),
    ],
)
def test_each_leak_is_named(text: str, leak: str) -> None:
    assert sanitize_history.leaks(text) == [leak]


def test_placeholders_are_not_leaks() -> None:
    assert sanitize_history.leaks("/work/a.py, ~/x, git push, dev@example.com") == []


def test_every_committed_history_is_clean() -> None:
    histories = sorted((ROOT / "evals").rglob("history.jsonl"))
    assert histories
    dirty = {str(p): found for p in histories if (found := sanitize_history.leaks(p.read_text()))}
    assert dirty == {}


def test_main_writes_a_clean_history(tmp_path: Path) -> None:
    session, out = tmp_path / "s.jsonl", tmp_path / "history.jsonl"
    session.write_text("\n".join(SESSION), "utf-8")
    assert sanitize_history.main([str(session), str(out), "--cwd", CWD, "--home", HOME]) == 0
    assert len(out.read_text("utf-8").splitlines()) == 2


def test_main_refuses_to_write_a_leak(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    session, out = tmp_path / "s.jsonl", tmp_path / "history.jsonl"
    session.write_text(_row(type="user", message={"content": "ping bob@corp.io"}), "utf-8")
    assert sanitize_history.main([str(session), str(out), "--cwd", CWD, "--home", HOME]) == 1
    assert not out.exists()
    assert "e-mail" in capsys.readouterr().err
