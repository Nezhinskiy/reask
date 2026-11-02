import json
import subprocess
from pathlib import Path

import pytest

from scripts import build_evals, record_scenario

ROOT = Path(__file__).resolve().parent.parent
SCENARIO = next(s for s in build_evals.load() if s.name == "rate-limit-compacted")


def _assistant(text: str, sidechain: bool = False) -> str:
    content = [{"type": "tool_use"}, {"type": "text", "text": text}]
    return json.dumps(
        {"type": "assistant", "isSidechain": sidechain, "message": {"content": content}}
    )


def test_isolation_prefers_bare_with_an_api_key() -> None:
    assert record_scenario.isolation({"ANTHROPIC_API_KEY": "k"}) == ["--bare"]
    assert "--strict-mcp-config" in record_scenario.isolation({})


def test_the_first_turn_names_the_session_and_later_turns_resume_it() -> None:
    first = record_scenario.command({"prompt": "read it"}, "s1", True, {})
    later = record_scenario.command({"command": "/compact"}, "s1", False, {})
    assert first[:5] == ["claude", "-p", "read it", "--session-id", "s1"]
    assert later[:5] == ["claude", "-p", "/compact", "--resume", "s1"]
    assert first[first.index("--tools") + 1 : first.index("--output-format")] == [
        "Read",
        "Glob",
        "Grep",
    ]


def test_final_message_is_the_last_main_thread_text() -> None:
    session = "\n".join(
        [_assistant("first"), "", _assistant("from a subagent", True), _assistant("the question")]
    )
    assert record_scenario.final_message(session) == "the question"


def _fake(config: Path, fail_at: int | None = None) -> record_scenario.Runner:
    calls: list[list[str]] = []

    def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        session = argv[argv.index("--session-id") + 1] if "--session-id" in argv else argv[4]
        path = record_scenario.session_file(config, cwd, session)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(_assistant(f"reply to {argv[2]}") + "\n")
        code = 1 if fail_at is not None and len(calls) - 1 == fail_at else 0
        return subprocess.CompletedProcess(argv, code, "", "boom" if code else "")

    run.calls = calls  # type: ignore[attr-defined]
    return run


def test_record_runs_every_step_and_keeps_the_attempt(tmp_path: Path) -> None:
    run = _fake(tmp_path / "config")
    dest = record_scenario.record(
        SCENARIO, tmp_path / "out", 2, run, {"CLAUDE_CONFIG_DIR": str(tmp_path / "config")}
    )
    assert dest == tmp_path / "out" / "rate-limit-compacted" / "2"
    assert len(run.calls) == 3  # type: ignore[attr-defined]
    assert (dest / "final.md").read_text("utf-8").startswith("reply to Next is API-88")
    scratch = Path((dest / "scratch.txt").read_text("utf-8"))
    assert (scratch / "deploy" / "k8s.yaml").is_file()
    assert ROOT not in scratch.parents


def test_record_stops_at_a_failed_step_and_logs_it(tmp_path: Path) -> None:
    run = _fake(tmp_path / "config", fail_at=0)
    dest = record_scenario.record(
        SCENARIO, tmp_path / "out", 1, run, {"CLAUDE_CONFIG_DIR": str(tmp_path / "config")}
    )
    log = json.loads((dest / "log.json").read_text("utf-8"))
    assert [entry["returncode"] for entry in log] == [1]
    assert log[0]["stderr"] == "boom"


def test_record_without_a_session_file_leaves_no_final(tmp_path: Path) -> None:
    def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "", "")

    dest = record_scenario.record(SCENARIO, tmp_path / "out", 1, run, {})
    assert not (dest / "final.md").exists()


def test_main_rejects_an_unknown_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    assert record_scenario.main(["nope"]) == 1
    assert "no scenario named nope" in capsys.readouterr().err


def test_main_records_each_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_record(scenario: build_evals.Scenario, out: Path, n: int) -> Path:
        dest = out / str(n)
        dest.mkdir(parents=True)
        if n == 1:
            (dest / "final.md").write_text("q", "utf-8")
        return dest

    monkeypatch.setattr(record_scenario, "record", fake_record)
    args = ["rate-limit-compacted", "--attempts", "2", "--out", str(tmp_path)]
    assert record_scenario.main(args) == 0
    out = capsys.readouterr().out
    assert "1: recorded" in out
    assert "2: no session file" in out
