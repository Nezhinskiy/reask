"""Read one partner file into dict rows. Every partner file is opened the same way."""

import csv
from pathlib import Path

DELIMITERS = {"kedr-pos": ";"}


def parse_file(partner: str, path: Path) -> list[dict]:
    delimiter = DELIMITERS.get(partner, ",")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = []
        for row in reader:
            rows.append(row)
    return rows
