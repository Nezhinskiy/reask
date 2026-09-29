"""Check the skill package: one skill folder, its frontmatter, the plugin manifests, one version.

The version is written in three places: SKILL.md's metadata.version (which is also the Python
package's version, through pyproject.toml's [tool.hatch.version]), .claude-plugin/plugin.json,
and CHANGELOG.md's newest release heading. When given, the release tag is a fourth. All must agree.
Run with no arguments in CI and with `--tag vX.Y.Z` in the release workflow.

The frontmatter is read with regular expressions rather than a YAML parser, to keep the project
free of dependencies. That is why the description must be one double-quoted line.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from scripts import release_notes

ROOT = Path(__file__).resolve().parent.parent
NAME = "reask"
SKILL = Path("skills") / NAME / "SKILL.md"
DESCRIPTION_LIMIT = 1024  # the Agent Skills specification's cap
IGNORED = {".git", ".venv", "build", "dist"}


def _frontmatter(skill: str) -> str | None:
    match = re.match(r"\A---\n(.*?)\n---\n", skill, re.S)
    return match.group(1) if match else None


def _field(frontmatter: str, pattern: str) -> str | None:
    match = re.search(pattern, frontmatter, re.M)
    return match.group(1) if match else None


def _json(root: Path, name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((root / ".claude-plugin" / name).read_text("utf-8"))
    return data


def versions(root: Path) -> dict[str, str | None]:
    frontmatter = _frontmatter((root / SKILL).read_text(encoding="utf-8")) or ""
    return {
        "SKILL.md metadata.version": _field(frontmatter, r'^\s+version:\s*"([^"]+)"\s*$'),
        ".claude-plugin/plugin.json": _json(root, "plugin.json").get("version"),
        "CHANGELOG.md's newest release": release_notes.latest(
            (root / "CHANGELOG.md").read_text(encoding="utf-8")
        ),
    }


def structure(root: Path) -> list[str]:
    problems = []
    skills = sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("SKILL.md")
        if not IGNORED & set(p.relative_to(root).parts)
    )
    if skills != [SKILL.as_posix()]:
        problems.append(f"expected exactly one skill, {SKILL.as_posix()}; found {skills}")
        if not (root / SKILL).is_file():
            return problems
    frontmatter = _frontmatter((root / SKILL).read_text(encoding="utf-8"))
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
    # The plugin finds the skill through the default skills/ directory; a "skills" override
    # would load something else.
    plugin = _json(root, "plugin.json")
    if plugin.get("name") != NAME or "skills" in plugin:
        problems.append(f'plugin.json must be named {NAME!r} and must not override "skills"')
    market = _json(root, "marketplace.json")
    entries = [(p.get("name"), p.get("source")) for p in market.get("plugins", [])]
    if entries != [(NAME, "./")]:
        problems.append(f'marketplace.json must list one plugin {NAME!r} with source "./"')
    return problems


def check(root: Path, tag: str | None = None) -> list[str]:
    problems = structure(root)
    if not (root / SKILL).is_file():
        return problems
    found = versions(root)
    expected = found["SKILL.md metadata.version"]
    if tag is not None:
        found["tag"] = tag[1:] if tag.startswith("v") else None
    problems += [
        f"{name}: {value!r} != SKILL.md's {expected!r}"
        for name, value in found.items()
        if value != expected
    ]
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if expected is not None and release_notes.notes(changelog, expected) is None:
        problems.append(f"CHANGELOG.md has no release notes for {expected}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="the release tag, vX.Y.Z")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    problems = check(args.root, args.tag)
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if not problems:
        version = versions(args.root)["SKILL.md metadata.version"]
        print(f"skill package ok, one version everywhere: {version}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
