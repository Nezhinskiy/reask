"""Check the skill package: one SKILL.md, its frontmatter, the plugin manifests, one version.

The version lives in pyproject.toml, uv.lock, .claude-plugin/plugin.json, SKILL.md's
metadata.version, CHANGELOG.md's first heading and, when given, the release tag; all must agree.
`__version__` is read from the installed metadata, so it cannot drift and is not a source here.
Run with no arguments in CI and with `--tag vX.Y.Z` in the release workflow.
"""

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "reask"
DESCRIPTION_LIMIT = 1024  # the Agent Skills specification's cap


def _frontmatter(skill: str) -> str | None:
    match = re.match(r"\A---\n(.*?)\n---\n", skill, re.S)
    return match.group(1) if match else None


def _field(frontmatter: str, pattern: str) -> str | None:
    match = re.search(pattern, frontmatter, re.M)
    return match.group(1) if match else None


def versions(root: Path) -> dict[str, str | None]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    locked = next((p["version"] for p in lock["package"] if p["name"] == project["name"]), None)
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    frontmatter = _frontmatter((root / "SKILL.md").read_text(encoding="utf-8")) or ""
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    return {
        "pyproject.toml": project["version"],
        "uv.lock": locked,
        ".claude-plugin/plugin.json": plugin.get("version"),
        "SKILL.md metadata.version": _field(frontmatter, r'^\s+version:\s*"?([^"\s]+)"?\s*$'),
        "CHANGELOG.md (first released ## heading)": _field(changelog, r"^## (?!Unreleased\b)(\S+)"),
    }


def structure(root: Path) -> list[str]:
    problems = []
    skills = sorted(
        str(p.relative_to(root))
        for p in root.rglob("SKILL.md")
        if not {".git", ".venv", "dist"} & set(p.relative_to(root).parts)
    )
    if skills != ["SKILL.md"]:
        problems.append(f"expected one SKILL.md at the root, found {skills}")
    frontmatter = _frontmatter((root / "SKILL.md").read_text(encoding="utf-8"))
    if frontmatter is None:
        return [*problems, "SKILL.md must begin with YAML frontmatter"]
    if _field(frontmatter, r"^name:\s*(\S+)\s*$") != NAME:
        problems.append(f"SKILL.md name must be {NAME!r}")
    description = _field(frontmatter, r'^description:\s*"((?:[^"\\]|\\.)*)"\s*$')
    if description is None:
        problems.append("SKILL.md description must be one double-quoted line")
    elif len(description) > DESCRIPTION_LIMIT:
        problems.append(
            f"SKILL.md description is {len(description)} chars, over {DESCRIPTION_LIMIT}"
        )
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    if plugin.get("name") != NAME or plugin.get("skills") != ["./"]:
        problems.append(f'plugin.json must be named {NAME!r} with "skills": ["./"]')
    entries = [(p.get("name"), p.get("source")) for p in market.get("plugins", [])]
    if entries != [(NAME, "./")]:
        problems.append(f'marketplace.json must list one plugin {NAME!r} with source "./"')
    return problems


def check(root: Path, tag: str | None = None) -> list[str]:
    found = versions(root)
    if tag is not None:
        found["tag"] = tag.removeprefix("v") if tag.startswith("v") else None
    expected = found["pyproject.toml"]
    mismatched = [
        f"{name}: {value!r} != pyproject.toml's {expected!r}"
        for name, value in found.items()
        if value != expected
    ]
    return structure(root) + mismatched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="the release tag, vX.Y.Z")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    problems = check(args.root, args.tag)
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if not problems:
        print(f"skill package ok, one version everywhere: {versions(args.root)['pyproject.toml']}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
