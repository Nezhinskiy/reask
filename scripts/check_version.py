"""One version everywhere: pyproject.toml, uv.lock, CHANGELOG.md and, when given, the tag.

`__version__` is read from the installed metadata, so it cannot drift and is not a source here.
Run with no arguments in CI and with `--tag vX.Y.Z` in the release workflow.
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sources(root: Path) -> dict[str, str | None]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    locked = next((p["version"] for p in lock["package"] if p["name"] == project["name"]), None)
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = re.search(r"^## (\S+)", changelog, re.M)
    return {
        "pyproject.toml": project["version"],
        "uv.lock": locked,
        "CHANGELOG.md (first ## heading)": heading.group(1) if heading else None,
    }


def check(root: Path, tag: str | None = None) -> list[str]:
    found = sources(root)
    if tag is not None:
        found["tag"] = tag.removeprefix("v") if tag.startswith("v") else None
    expected = found["pyproject.toml"]
    return [
        f"{name}: {value!r} != pyproject.toml's {expected!r}"
        for name, value in found.items()
        if value != expected
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="the release tag, vX.Y.Z")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    problems = check(args.root, args.tag)
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if not problems:
        print(f"one version everywhere: {sources(args.root)['pyproject.toml']}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
