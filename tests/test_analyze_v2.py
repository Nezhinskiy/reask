import json
from pathlib import Path
from typing import Any

import pytest

from scripts import analyze_v2


def _run(passed: dict[str, bool], words: int = 10, error: str | None = None) -> dict[str, Any]:
    reply = " ".join(["w"] * words)
    return {
        "costUsd": 0.5,
        "error": error,
        "graders": [{"name": n, "passed": p, "evidence": reply} for n, p in passed.items()],
    }


GOOD = {"facts": True, "decision-1": True, "all-decisions": True, "no-trap-pick": True}
BAD = {**GOOD, "decision-1": False}
DIAG = {"references": False}


def _result() -> dict[str, Any]:
    return {
        "cases": [
            {
                "name": "s1-short",
                "arms": {
                    "with": [_run({**GOOD, **DIAG}, 300), _run(GOOD, 320)],
                    "without": [_run(BAD, 100), _run(BAD, 120)],
                },
            },
            {
                "name": "s1-manual",
                "arms": {"with": [_run(GOOD, 400)], "without": [_run(GOOD, 240), _run(BAD)]},
            },
            {
                "name": "s2-short",
                "arms": {"with": [_run(GOOD)], "without": [_run(GOOD, error="timeout")]},
            },
            {"name": "s1-trigger-decided", "arms": {"with": [{"graders": [], "costUsd": 0.1}]}},
            {"name": "s1-trigger-confused", "arms": {"with": [_run({"skill-loads": False})]}},
            {"name": "unrelated", "arms": {"with": [_run(GOOD)]}},
        ]
    }


def test_runs_are_mapped_to_cells_and_closed_only_on_outcome_graders() -> None:
    rows = analyze_v2.runs([_result()])
    cells = [(r["scenario"], r["cell"], r["closed"]) for r in rows if r["kind"] == "short"]
    assert cells == [
        ("s1", "B", True),
        ("s1", "B", True),
        ("s1", "A", False),
        ("s1", "A", False),
        ("s2", "B", True),
        ("s2", "A", False),
    ]
    assert {r["cell"] for r in rows if r["kind"] == "manual"} == {"C", "D"}
    assert rows[0]["words"] == 300


def test_summary_counts_cells_scenarios_and_hypotheses() -> None:
    s = analyze_v2.summarise(analyze_v2.runs([_result()]))
    assert (s["cells"]["B"]["closed"], s["cells"]["B"]["runs"]) == (3, 3)
    assert s["cells"]["A"]["share"] == 0
    assert s["cells"]["B"]["graders"]["references"] == 0
    assert s["cells"]["B"]["median_words_closed"] == 300
    assert s["scenarios"]["s1"]["C"] == {
        "runs": 2,
        "closed": 1,
        "share": 0.5,
        "median_words": 125.0,
        "pass_k": False,
    }
    assert s["scenarios"]["s2"]["C"]["share"] is None
    assert s["B_vs_A"]["better"] == 2
    assert s["B_vs_C"]["scenarios"] == 1
    assert s["H2"] == {"closed_ok": True, "words_ok": False}
    assert s["triggers"] == {
        "trigger-decided": {"runs": 1, "passed": 1},
        "trigger-confused": {"runs": 1, "passed": 0},
    }


def test_h2_is_open_without_both_cells() -> None:
    rows = [r for r in analyze_v2.runs([_result()]) if r["cell"] != "C"]
    assert analyze_v2.summarise(rows)["H2"] is None


def test_wilson_and_sign_test() -> None:
    assert analyze_v2.wilson(0, 0) == (0.0, 1.0)
    lo, hi = analyze_v2.wilson(9, 10)
    assert 0.59 < lo < 0.6
    assert hi > 0.98
    assert analyze_v2.sign_test([0.0, 0.0]) == 1.0
    assert analyze_v2.sign_test([1.0] * 8) == pytest.approx(2 / 256)
    assert analyze_v2.sign_test([1.0, -1.0]) == 1.0


def test_main_writes_summary_and_replies(tmp_path: Path) -> None:
    result = tmp_path / "r.json"
    result.write_text(json.dumps(_result()), "utf-8")
    assert analyze_v2.main([str(tmp_path / "out"), str(result)]) == 0
    assert (tmp_path / "out" / "replies" / "s1-short-B-1.md").is_file()
    data = json.loads((tmp_path / "out" / "summary.json").read_text("utf-8"))
    assert "reply" not in data["runs"][0]
    assert "| B | 3/3 (100%)" in (tmp_path / "out" / "summary.md").read_text("utf-8")


def test_main_rejects_results_without_v2_runs(tmp_path: Path) -> None:
    result = tmp_path / "r.json"
    result.write_text(json.dumps({"cases": []}), "utf-8")
    assert analyze_v2.main([str(tmp_path / "out"), str(result)]) == 1
