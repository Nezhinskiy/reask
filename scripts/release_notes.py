"""Print the CHANGELOG.md section for a release tag, without its heading, as the Release notes."""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def notes(changelog: str, tag: str) -> str | None:
    version = tag.removeprefix("v")
    match = re.search(rf"^## {re.escape(version)} .*?(?=^## |\Z)", changelog, re.S | re.M)
    if match is None:
        return None
    return match.group(0).split("\n", 1)[1].strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="the release tag, vX.Y.Z")
    parser.add_argument("--changelog", type=Path, default=ROOT / "CHANGELOG.md")
    args = parser.parse_args(argv)
    found = notes(args.changelog.read_text(encoding="utf-8"), args.tag)
    if not found:
        print(
            f"::error::{args.changelog.name} has no non-empty section for {args.tag}",
            file=sys.stderr,
        )
        return 1
    print(found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
