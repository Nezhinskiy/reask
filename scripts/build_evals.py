"""Build the v2 benchmark's eval cases from its scenarios, or check the scenarios are complete.

Each scenario in evals/v2/scenarios/<name>/ is the one source of truth for its cases:
scenario.toml (the hidden truth and the graders' inputs), project/ (the fixture the agent reads)
and, once recorded, history.jsonl (the session up to the agent's pending question). This script
renders the cases `claude plugin eval` runs:

- <name>-short and <name>-manual: the main cells (A/B and C/D), with the scenario's graders;
- <name>-trigger-decided, -proceed, -confused: does the skill load when it should, and only then.

    python -m scripts.build_evals check            # every scenario has its stage-1 truth (CI)
    python -m scripts.build_evals build evals-build  # render cases for recorded, frozen scenarios
    claude plugin eval . --eval-dir evals-build --tag main ...

The cases are rendered, not committed, so the scenario stays the only copy of each fact.
"""

import argparse
import json
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / "evals" / "v2"
LANGUAGES = {"en": "English", "ru": "Russian"}
TOOLS = ["Read", "Glob", "Grep", "Skill"]
MAX_TURNS = 20
RUNS = 5
SKILL_CALL = r'"skill"\s*:\s*"(?:[\w-]+:)?reask"'
# A reply to "go with your recommendation" should confirm in a line or two, not brief again.
# The harness matches in JavaScript: no \A or \Z; without the m flag ^ and $ bound the message.
SHORT_REPLY = r"^\s*(?:\S+\s+){0,60}\S*\s*$"
STAGE1 = {
    "summary": str,
    "language": str,
    "shape": list,
    "record": dict,
    "trap": dict,
    "persona": dict,
}
TRAP = ("fact", "file", "wrong_pick")


@dataclass(frozen=True)
class Scenario:
    name: str
    path: Path
    data: dict[str, Any]

    @property
    def language(self) -> str:
        return str(self.data["language"])

    @property
    def recorded(self) -> bool:
        return (self.path / "history.jsonl").is_file()

    @property
    def stage2(self) -> dict[str, Any]:
        """The truth written from the recorded question, before any re-ask was run."""
        return dict(self.data.get("stage2", {}))

    @property
    def frozen(self) -> bool:
        return bool(self.stage2.get("decisions")) and bool(self.stage2.get("facts"))


def load(root: Path = V2) -> list[Scenario]:
    scenarios = []
    for toml in sorted((root / "scenarios").glob("*/scenario.toml")):
        data = tomllib.loads(toml.read_text("utf-8"))
        scenarios.append(Scenario(toml.parent.name, toml.parent, data))
    return scenarios


def problems(s: Scenario) -> list[str]:
    """What stops a scenario from being recorded (stage 1) or built (stage 2)."""
    out = [
        f"{s.name}: missing or wrong {key}"
        for key, kind in STAGE1.items()
        if not isinstance(s.data.get(key), kind)
    ]
    if out:
        return out
    if s.language not in LANGUAGES:
        out.append(f"{s.name}: language must be one of {sorted(LANGUAGES)}")
    if not s.data["record"].get("steps") or not s.data["record"].get("select"):
        out.append(f"{s.name}: record needs steps and a select rule")
    if any(not s.data["trap"].get(k) for k in TRAP):
        out.append(f"{s.name}: trap needs {', '.join(TRAP)}")
    elif not (s.path / s.data["trap"]["file"]).is_file():
        out.append(f"{s.name}: trap file {s.data['trap']['file']} does not exist")
    if not s.data["persona"].get("situation"):
        out.append(f"{s.name}: persona needs a situation")
    if not (s.path / "project").is_dir():
        out.append(f"{s.name}: no project/ fixture")
    if s.frozen and not s.recorded:
        out.append(f"{s.name}: decisions and facts are frozen before a question was recorded")
    for d in s.stage2.get("decisions", []):
        if not d.get("ask"):
            out.append(f"{s.name}: every decision needs an ask")
    return out


def _bullets(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


def _needs(decision: dict[str, Any]) -> str:
    if decision.get("needs"):
        return (
            "the message makes it clear which offered option is "
            f"{decision['needs']}, so that you can pick it"
        )
    return "the message tells you what each option costs and what it gets you"


def graders(s: Scenario, templates: Path) -> dict[str, str]:
    t = {p.stem: p.read_text("utf-8") for p in templates.glob("*.md")}
    d, truth = s.data, s.stage2
    answered = truth.get("answered", [])
    out = {
        "facts": t["facts"].format(facts=_bullets(truth["facts"])),
        "all-decisions": t["all-decisions"].format(
            decisions=_bullets([x["ask"] for x in truth["decisions"]]),
            answered=(
                "\nIt must not ask again about these, which the user already answered:\n\n"
                + _bullets(answered)
                + "\n"
                if answered
                else ""
            ),
        ),
        "no-trap-pick": t["no-trap-pick"].format(
            wrong_pick=d["trap"]["wrong_pick"], trap_fact=d["trap"]["fact"]
        ),
    }
    for i, decision in enumerate(truth["decisions"], 1):
        out[f"decision-{i}"] = t["decision"].format(
            situation=d["persona"]["situation"], decision=decision["ask"], needs=_needs(decision)
        )
    if d.get("codes"):
        out["references"] = t["references"].format(codes=_bullets(d["codes"]))
    if d.get("check_language"):
        out["language"] = t["language"].format(language=LANGUAGES[s.language])
    return out


def _case_yaml(name: str, description: str, tags: list[str], prompt: str, runs: int) -> str:
    # JSON strings are valid YAML scalars, which keeps prompts with quotes and colons intact.
    return (
        'schema_version: "1.1"\n'
        f"name: {name}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"runs: {runs}\n"
        "context:\n"
        "  history_file: history.jsonl\n"
        "  add_dirs: [project]\n"
        "execution:\n"
        f"  max_turns: {MAX_TURNS}\n"
        f"  allowed_tools: [{', '.join(TOOLS)}]\n"
        f"  prompt: {json.dumps(prompt, ensure_ascii=False)}\n"
    )


def _skill_grader(min_: int | None = None, max_: int | None = None) -> str:
    # min defaults to 1 in the harness, so "never" needs min: 0 as well as max: 0.
    bound = f"min: {min_}\n" if min_ is not None else f"min: 0\nmax: {max_}\n"
    return f"---\ntype: tool_used\ntool: Skill\ninput_match: '{SKILL_CALL}'\n{bound}---\n"


def cases(s: Scenario, prompts: dict[str, dict[str, str]], templates: Path) -> dict[str, Any]:
    """Every case of one scenario: name -> (case.yaml, {grader name: text})."""
    lang = s.language
    main = graders(s, templates)
    out: dict[str, Any] = {}
    for cell in ("short", "manual"):
        out[f"{s.name}-{cell}"] = (
            _case_yaml(
                f"{s.name}-{cell}", s.data["summary"], ["main", cell], prompts[cell][lang], RUNS
            ),
            main,
        )
    triggers = {
        "decided": {
            "skill-silent": _skill_grader(max_=0),
            "short-reply": f"---\ntype: regex\npattern: '{SHORT_REPLY}'\n---\n",
        },
        "proceed": {"skill-silent": _skill_grader(max_=0)},
        "confused": {"skill-loads": _skill_grader(min_=1)},
    }
    for kind, trigger_graders in triggers.items():
        name = f"{s.name}-trigger-{kind}"
        out[name] = (
            _case_yaml(name, s.data["summary"], ["trigger", kind], prompts[kind][lang], RUNS),
            trigger_graders,
        )
    return out


def build(out_dir: Path, root: Path = V2) -> list[str]:
    prompts = tomllib.loads((root / "prompts.toml").read_text("utf-8"))
    built = []
    for s in load(root):
        if problems(s) or not (s.recorded and s.frozen):
            continue
        for name, (case_yaml, grader_texts) in cases(s, prompts, root / "graders").items():
            case = out_dir / name
            if case.exists():
                shutil.rmtree(case)
            shutil.copytree(s.path / "project", case / "project")
            shutil.copy(s.path / "history.jsonl", case / "history.jsonl")
            (case / "case.yaml").write_text(case_yaml, "utf-8")
            (case / "graders").mkdir()
            for grader, text in grader_texts.items():
                (case / "graders" / f"{grader}.md").write_text(text, "utf-8")
            built.append(name)
    return built


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    b = sub.add_parser("build")
    b.add_argument("out_dir", type=Path)
    args = parser.parse_args(argv)
    scenarios = load()
    found = [p for s in scenarios for p in problems(s)]
    for p in found:
        print(p, file=sys.stderr)
    if args.command == "check":
        if not found:
            ready = sum(s.recorded and s.frozen for s in scenarios)
            print(f"{len(scenarios)} scenarios ok, {ready} recorded and frozen")
        return 1 if found or not scenarios else 0
    built = build(args.out_dir)
    print(f"built {len(built)} cases in {args.out_dir}")
    return 1 if found else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
