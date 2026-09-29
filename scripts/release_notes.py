"""Read CHANGELOG.md: its newest release, and a release's section as the GitHub Release notes.

A release heading is `## X.Y.Z (YYYY-MM-DD)`; `## Unreleased` and anything else is not one. Both
check_skill.py and the release workflow read the changelog through this module, so a heading one
of them accepts the other cannot reject.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADING = r"^## (?P<version>\d+\.\d+\.\d+) \(\d{4}-\d{2}-\d{2}\)$"


def latest(changelog: str) -> str | None:
    """Return the newest release's version: the first release heading."""
    match = re.search(HEADING, changelog, re.M)
    return match["version"] if match else None


def notes(changelog: str, version: str) -> str | None:
    """Return the body of `version`'s section, or None if it has no section or an empty one."""
    for match in re.finditer(rf"{HEADING}\n(?P<body>.*?)(?=^## |\Z)", changelog, re.M | re.S):
        if match["version"] == version:
            return match["body"].strip() or None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="the release tag, vX.Y.Z")
    parser.add_argument("--changelog", type=Path, default=ROOT / "CHANGELOG.md")
    args = parser.parse_args(argv)
    found = notes(args.changelog.read_text(encoding="utf-8"), args.tag.removeprefix("v"))
    if found is None:
        print(f"::error::{args.changelog.name} has no section for {args.tag}", file=sys.stderr)
        return 1
    print(found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
