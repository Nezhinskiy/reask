import shutil
import tomllib
from pathlib import Path

import pytest

from scripts import build_evals

ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / "evals" / "v2"
FROZEN = """
[stage2]
facts = ["six replicas", "a 100 per minute limit"]
answered = ["which CI provider"]

[[stage2.decisions]]
ask = "where the counters live"
needs = "the option that adds no service your team must run"

[[stage2.decisions]]
ask = "what a client over the limit gets"
"""


@pytest.fixture
def v2(tmp_path: Path) -> Path:
    """A copy of the real prompts and graders with one scenario, recorded and frozen."""
    root = tmp_path / "v2"
    shutil.copytree(V2 / "graders", root / "graders")
    shutil.copy(V2 / "prompts.toml", root / "prompts.toml")
    s = root / "scenarios" / "demo"
    shutil.copytree(V2 / "scenarios" / "rate-limit-compacted", s)
    text = (s / "scenario.toml").read_text("utf-8")
    text = text.replace('codes = ["API-88", "INC-412"]', 'codes = ["API-88"]')
    text = text.replace("check_language = false", "check_language = true")
    (s / "scenario.toml").write_text(text + FROZEN, "utf-8")
    (s / "history.jsonl").write_text('{"type": "user"}\n', "utf-8")
    return root


def _scenario(v2: Path) -> build_evals.Scenario:
    [s] = build_evals.load(v2)
    return s


def _edit(v2: Path, old: str, new: str) -> None:
    path = v2 / "scenarios" / "demo" / "scenario.toml"
    path.write_text(path.read_text("utf-8").replace(old, new), "utf-8")


def test_the_committed_scenarios_are_complete() -> None:
    assert build_evals.main(["check"]) == 0


def test_a_recorded_frozen_scenario_has_no_problems(v2: Path) -> None:
    s = _scenario(v2)
    assert (s.recorded, s.frozen, build_evals.problems(s)) == (True, True, [])


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        ('language = "en"', "language = 1", "missing or wrong language"),
        ('language = "en"', 'language = "de"', "language must be one of"),
        ("select = ", "selected = ", "record needs steps and a select rule"),
        ('wrong_pick = "', 'wrong = "', "trap needs fact, file, wrong_pick"),
        ('"project/deploy/k8s.yaml"', '"project/nowhere.yaml"', "does not exist"),
        ("situation = ", "story = ", "persona needs a situation"),
        ('ask = "what a client', 'question = "what a client', "every decision needs an ask"),
    ],
)
def test_each_stage_one_gap_is_named(v2: Path, old: str, new: str, problem: str) -> None:
    _edit(v2, old, new)
    assert any(problem in p for p in build_evals.problems(_scenario(v2)))


def test_a_scenario_without_a_fixture_is_named(v2: Path) -> None:
    shutil.rmtree(v2 / "scenarios" / "demo" / "project")
    _edit(v2, '"project/deploy/k8s.yaml"', '"scenario.toml"')
    assert build_evals.problems(_scenario(v2)) == ["demo: no project/ fixture"]


def test_truth_frozen_before_a_recording_is_refused(v2: Path) -> None:
    (v2 / "scenarios" / "demo" / "history.jsonl").unlink()
    assert build_evals.problems(_scenario(v2)) == [
        "demo: decisions and facts are frozen before a question was recorded"
    ]


def test_graders_carry_the_scenario_truth(v2: Path) -> None:
    g = build_evals.graders(_scenario(v2), v2 / "graders")
    assert sorted(g) == [
        "all-decisions",
        "decision-1",
        "decision-2",
        "facts",
        "language",
        "no-trap-pick",
        "references",
    ]
    assert "1. six replicas\n2. a 100 per minute limit" in g["facts"]
    assert "1. where the counters live\n2. what a client over the limit gets" in g["all-decisions"]
    assert "already answered:\n\n1. which CI provider" in g["all-decisions"]
    assert "the option that adds no service your team must run, so" in g["decision-1"]
    assert "promised the on-call lead" in g["decision-1"]
    assert "what each option costs" in g["decision-2"]
    assert "6 replicas" in g["no-trap-pick"]
    assert "1. API-88" in g["references"]
    assert "written in English" in g["language"]
    assert all("{" not in text for text in g.values())


def test_optional_graders_are_left_out_when_they_would_pass_by_default(v2: Path) -> None:
    _edit(v2, 'codes = ["API-88"]', "codes = []")
    _edit(v2, "check_language = true", "check_language = false")
    _edit(v2, 'answered = ["which CI provider"]', "answered = []")
    g = build_evals.graders(_scenario(v2), v2 / "graders")
    assert "references" not in g
    assert "language" not in g
    assert "already answered" not in g["all-decisions"]


def test_cases_pair_each_cell_with_the_same_graders(v2: Path) -> None:
    prompts = tomllib.loads((v2 / "prompts.toml").read_text("utf-8"))
    cases = build_evals.cases(_scenario(v2), prompts, v2 / "graders")
    short_yaml, short_graders = cases["demo-short"]
    manual_yaml, manual_graders = cases["demo-manual"]
    assert short_graders is manual_graders
    assert "tags: [main, short]" in short_yaml
    assert f'prompt: "{prompts["short"]["en"]}"' in short_yaml
    assert "check the fact your recommendation rests" in manual_yaml
    assert "max_turns: 20" in manual_yaml
    assert "allowed_tools: [Read, Glob, Grep, Skill]" in manual_yaml
    assert sorted(cases) == [
        "demo-manual",
        "demo-short",
        "demo-trigger-confused",
        "demo-trigger-decided",
        "demo-trigger-proceed",
    ]
    _, decided = cases["demo-trigger-decided"]
    assert "max: 0" in decided["skill-silent"]
    assert "type: regex" in decided["short-reply"]
    _, confused = cases["demo-trigger-confused"]
    assert "min: 1" in confused["skill-loads"]


def test_build_renders_runnable_case_folders(v2: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    (out / "demo-short").mkdir(parents=True)
    (out / "demo-short" / "stale.md").write_text("from an earlier build", "utf-8")
    built = build_evals.build(out, v2)
    assert len(built) == 5
    case = out / "demo-short"
    assert not (case / "stale.md").exists()
    assert (case / "project" / "deploy" / "k8s.yaml").is_file()
    assert (case / "history.jsonl").read_text("utf-8") == '{"type": "user"}\n'
    assert (case / "graders" / "decision-2.md").is_file()
    assert (case / "case.yaml").read_text("utf-8").startswith('schema_version: "1.1"\n')


def test_build_skips_scenarios_not_yet_recorded(v2: Path, tmp_path: Path) -> None:
    _edit(v2, "facts = ", "unfrozen = ")
    assert build_evals.build(tmp_path / "out", v2) == []


def test_main_reports_problems_and_counts(
    v2: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    real_load = build_evals.load
    monkeypatch.setattr(build_evals, "load", lambda root=v2: real_load(v2))
    assert build_evals.main(["check"]) == 0
    assert "1 scenarios ok, 1 recorded and frozen" in capsys.readouterr().out
    monkeypatch.setattr(build_evals, "build", lambda out: ["x"])
    assert build_evals.main(["build", str(tmp_path)]) == 0
    _edit(v2, "situation = ", "story = ")
    assert build_evals.main(["check"]) == 1
    assert build_evals.main(["build", str(tmp_path)]) == 1
    assert "persona needs a situation" in capsys.readouterr().err


def test_check_fails_when_there_are_no_scenarios(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_evals, "load", lambda root=V2: [])
    assert build_evals.main(["check"]) == 1
