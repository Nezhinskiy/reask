"""Nightly ingest: one CSV per partner per day -> the transactions table."""

import argparse
import logging
from datetime import date, timedelta
from pathlib import Path

from ingest.db import upsert_transactions
from ingest.parse import parse_file

log = logging.getLogger("ingest")
PARTNERS = ["brewline", "kedr-pos", "lumen-pos"]
SFTP_ROOT = Path("/srv/sftp")
FILE_NAMES = {
    "brewline": "brewline-{d:%Y-%m-%d}.csv",
    "kedr-pos": "kedr_{d:%Y%m%d}.csv",
    "lumen-pos": "lumen_{d:%Y%m%d}.csv",
}


def sftp_path(partner: str, day: date) -> Path:
    return SFTP_ROOT / partner / FILE_NAMES[partner].format(d=day)


def main(day: date, only: str | None = None) -> None:
    for partner in [only] if only else PARTNERS:
        rows = parse_file(partner, sftp_path(partner, day))  # any error fails the whole run
        n = upsert_transactions(partner, rows)  # keyed on (partner, receipt_id)
        log.info("loaded partner=%s rows=%d", partner, n)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=date.fromisoformat,
                        default=date.today() - timedelta(days=1))
    parser.add_argument("--partner")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main(args.date, args.partner)
