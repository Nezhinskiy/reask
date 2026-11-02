"""Summarise v2 runs: closed-in-one per cell and scenario, words, paired tests, trigger rates.

    python -m scripts.analyze_v2 OUT_DIR RESULT.json [RESULT.json ...]

Reads the harness's aggregate-result.json files (or --json output). A main case is
<scenario>-short (cells A without the plugin, B with it) or <scenario>-manual (C, D); a run is
closed when every outcome grader passed (facts, every decision-N, all-decisions, no-trap-pick).
Writes OUT_DIR/summary.json, OUT_DIR/summary.md and every reply under OUT_DIR/replies/.
"""

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any

CELLS = {("short", "without"): "A", ("short", "with"): "B", ("manual", "without"): "C"}
CELLS[("manual", "with")] = "D"
OUTCOME = re.compile(r"^(facts|decision-\d+|all-decisions|no-trap-pick)$")
READING_WPM = 238


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def sign_test(diffs: list[float]) -> float:
    """Two-sided exact sign test over non-zero paired differences."""
    nonzero = [d for d in diffs if d != 0]
    n, k = len(nonzero), sum(d > 0 for d in nonzero)
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(k, n - k) + 1)) / 2**n
    return min(1.0, 2 * tail)


def runs(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every run as {scenario, kind, cell/trigger, closed, graders, words, reply, cost}."""
    out = []
    for result in results:
        for case in result["cases"]:
            m = re.match(r"^(.*)-(short|manual|trigger-\w+)$", case["name"])
            if not m:
                continue
            scenario, kind = m.groups()
            for arm, arm_runs in case.get("arms", {}).items():
                for i, run in enumerate(arm_runs):
                    graders = {g["name"]: bool(g["passed"]) for g in run.get("graders", [])}
                    reply = next(
                        (g["evidence"] for g in run.get("graders", []) if g.get("evidence")), ""
                    )
                    outcome = [v for k, v in graders.items() if OUTCOME.match(k)]
                    out.append(
                        {
                            "scenario": scenario,
                            "kind": kind,
                            "cell": CELLS.get((kind, arm), f"{kind}/{arm}"),
                            "run": i + 1,
                            "closed": bool(outcome) and all(outcome) and not run.get("error"),
                            "graders": graders,
                            "words": len(reply.split()),
                            "reply": reply,
                            "cost": run.get("costUsd", 0.0),
                            "error": run.get("error"),
                        }
                    )
    return out


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    main = [r for r in rows if r["cell"] in "ABCD" and len(r["cell"]) == 1]
    scenarios = sorted({r["scenario"] for r in main})
    table: dict[str, dict[str, Any]] = {}
    for s in scenarios:
        table[s] = {}
        for cell in "ABCD":
            rs = [r for r in main if r["scenario"] == s and r["cell"] == cell]
            closed = [r for r in rs if r["closed"]]
            table[s][cell] = {
                "runs": len(rs),
                "closed": len(closed),
                "share": len(closed) / len(rs) if rs else None,
                "median_words": statistics.median([r["words"] for r in rs]) if rs else None,
                "pass_k": bool(rs) and len(closed) == len(rs),
            }
    cells = {}
    for cell in "ABCD":
        rs = [r for r in main if r["cell"] == cell]
        k = sum(r["closed"] for r in rs)
        closed_words = [r["words"] for r in rs if r["closed"]]
        graders: dict[str, list[bool]] = {}
        for r in rs:
            for g, v in r["graders"].items():
                graders.setdefault(g.split("-")[0] if g.startswith("decision") else g, []).append(v)
        cells[cell] = {
            "runs": len(rs),
            "closed": k,
            "share": k / len(rs) if rs else None,
            "wilson95": wilson(k, len(rs)),
            "median_words": statistics.median([r["words"] for r in rs]) if rs else None,
            "median_words_closed": statistics.median(closed_words) if closed_words else None,
            "reading_minutes_closed": (
                statistics.median(closed_words) / READING_WPM if closed_words else None
            ),
            "graders": {g: sum(v) / len(v) for g, v in sorted(graders.items())},
            "cost": sum(r["cost"] for r in rs),
        }

    def paired(x: str, y: str) -> dict[str, Any]:
        diffs = [
            table[s][x]["share"] - table[s][y]["share"]
            for s in scenarios
            if table[s][x]["share"] is not None and table[s][y]["share"] is not None
        ]
        return {
            "scenarios": len(diffs),
            "better": sum(d > 0 for d in diffs),
            "worse": sum(d < 0 for d in diffs),
            "mean_diff": statistics.mean(diffs) if diffs else None,
            "sign_test_p": sign_test(diffs),
        }

    b, c = cells["B"], cells["C"]
    h2 = (
        None
        if b["share"] is None or c["share"] is None
        else {
            "closed_ok": b["share"] >= c["share"] - 0.10,
            "words_ok": (
                b["median_words_closed"] is not None
                and c["median_words_closed"] is not None
                and b["median_words_closed"] <= 1.2 * c["median_words_closed"]
            ),
        }
    )
    triggers: dict[str, dict[str, Any]] = {}
    for r in rows:
        if r["kind"].startswith("trigger-"):
            t = triggers.setdefault(r["kind"], {"runs": 0, "passed": 0})
            t["runs"] += 1
            t["passed"] += all(r["graders"].values()) and not r["error"]
    return {
        "cells": cells,
        "scenarios": table,
        "B_vs_A": paired("B", "A"),
        "B_vs_C": paired("B", "C"),
        "H2": h2,
        "triggers": triggers,
        "cost": sum(r["cost"] for r in rows),
    }


def markdown(summary: dict[str, Any]) -> str:
    def pct(v: float | None) -> str:
        return "-" if v is None else f"{v:.0%}"

    lines = ["| Cell | Closed in one | 95% CI | Median words (closed) |", "|---|---|---|---|"]
    for cell, c in summary["cells"].items():
        lo, hi = c["wilson95"]
        words = "-" if c["median_words_closed"] is None else f"{c['median_words_closed']:.0f}"
        lines.append(
            f"| {cell} | {c['closed']}/{c['runs']} ({pct(c['share'])}) | "
            f"{lo:.0%} to {hi:.0%} | {words} |"
        )
    lines += ["", "| Scenario | A | B | C | D |", "|---|---|---|---|---|"]
    for s, cells in summary["scenarios"].items():
        lines.append(f"| {s} | " + " | ".join(pct(cells[c]["share"]) for c in "ABCD") + " |")
    for name in ("B_vs_A", "B_vs_C"):
        p = summary[name]
        lines.append(
            f"\n{name}: better in {p['better']}, worse in {p['worse']} of "
            f"{p['scenarios']} scenarios; sign test p = {p['sign_test_p']:.3f}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("results", type=Path, nargs="+")
    args = parser.parse_args(argv)
    rows = runs([json.loads(p.read_text("utf-8")) for p in args.results])
    if not rows:
        print("no v2 runs found", file=sys.stderr)
        return 1
    summary = summarise(rows)
    replies = args.out / "replies"
    replies.mkdir(parents=True, exist_ok=True)
    for r in rows:
        if r["reply"]:
            name = f"{r['scenario']}-{r['kind']}-{r['cell'].replace('/', '-')}-{r['run']}.md"
            (replies / name).write_text(r["reply"] + "\n", "utf-8")
    slim = [{k: v for k, v in r.items() if k != "reply"} for r in rows]
    (args.out / "summary.json").write_text(
        json.dumps({"summary": summary, "runs": slim}, indent=1, ensure_ascii=False) + "\n",
        "utf-8",
    )
    (args.out / "summary.md").write_text(markdown(summary), "utf-8")
    print(markdown(summary))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
