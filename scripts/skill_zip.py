"""Build the skill zip that claude.ai accepts: a `reask/` folder holding SKILL.md and LICENSE.

Entries carry a fixed timestamp and permissions, so the same sources give the same bytes and
the attestation over the zip is reproducible.
"""

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ("SKILL.md", "LICENSE")
EPOCH = (1980, 1, 1, 0, 0, 0)


def build(destination: Path, root: Path = ROOT) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            info = zipfile.ZipInfo(f"reask/{name}", date_time=EPOCH)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (root / name).read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    build(args.destination)
    print(f"wrote {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
