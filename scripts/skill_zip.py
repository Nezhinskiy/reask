"""Build the skill zip that claude.ai accepts: a `reask/` folder holding the skill and LICENSE.

Entries carry zipfile's fixed default timestamp rather than the files' mtimes, so the same
sources always give the same bytes.
"""

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "reask"


def build(destination: Path) -> None:
    # The whole skill folder, as the other channels ship it, plus the licence it names.
    files = (p for p in SKILL.rglob("*") if p.is_file())
    entries = {f"reask/{p.relative_to(SKILL).as_posix()}": p for p in files}
    entries["reask/LICENSE"] = ROOT / "LICENSE"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, entries[name].read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    build(args.destination)
    print(f"wrote {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
