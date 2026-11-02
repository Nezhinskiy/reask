import json
from pathlib import Path

import pytest

from scripts import grade_external


@pytest.fixture
def cases(tmp_path: Path) -> Path:
    graders = tmp_path / "demo-short" / "graders"
    graders.mkdir(parents=True)
    (graders / "facts.md").write_text("---\ntype: llm\n---\nMentions six replicas.\n", "utf-8")
    (graders / "skill.md").write_text("---\ntype: tool_used\ntool: Skill\n---\n", "utf-8")
    (graders / "broken.md").write_text("no frontmatter", "utf-8")
    return tmp_path


def test_only_llm_graders_are_used(cases: Path) -> None:
    assert grade_external.llm_graders(cases / "demo-short") == {"facts": "Mentions six replicas."}


def test_votes_are_decided_by_majority(cases: Path) -> None:
    answers = iter([True, False, True, False, False, True])
    rows = [
        {"case": "demo-short", "label": "pos-1", "text": "six replicas"},
        {"case": "demo-short", "label": "neg-1", "text": "nothing"},
    ]
    result = grade_external.grade(cases, rows, lambda c, m: next(answers), votes=3, workers=1)
    assert result == [
        {"case": "demo-short", "label": "pos-1", "graders": {"facts": True}},
        {"case": "demo-short", "label": "neg-1", "graders": {"facts": False}},
    ]


def test_main_writes_verdicts(cases: Path, tmp_path: Path) -> None:
    messages, out = tmp_path / "m.jsonl", tmp_path / "out.json"
    messages.write_text(
        json.dumps({"case": "demo-short", "label": "q", "text": "six replicas"}) + "\n", "utf-8"
    )
    judge = lambda criterion, message: "six" in message  # noqa: E731
    assert grade_external.main([str(cases), str(messages), str(out)], judge) == 0
    assert json.loads(out.read_text("utf-8"))[0]["graders"] == {"facts": True}


def test_main_refuses_unknown_cases(
    cases: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    messages = tmp_path / "m.jsonl"
    messages.write_text(json.dumps({"case": "nope", "label": "q", "text": "x"}) + "\n", "utf-8")
    assert grade_external.main([str(cases), str(messages), str(tmp_path / "o.json")]) == 1
    assert "no such case: nope" in capsys.readouterr().err
