"""Onboarding step 3: import a school's bank statement (CSV) into ledger-api."""

import csv

from importer.ledger_client import post_entry, rollback
from importer.validate import validate_row

GENERIC_ERROR = "Не удалось загрузить файл. Попробуйте ещё раз"


def run_import(school, path):
    posted = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line_no, row in enumerate(csv.DictReader(f, delimiter=";"), start=2):
            try:
                entry = validate_row(school, row)
                posted.append(post_entry(school.id, entry))
            except Exception:
                # ONB-12: most failures here are ledger-api timeouts (see ONB-9);
                # a background retry could take care of them without bothering the school.
                rollback(posted)
                return {"ok": False, "message": GENERIC_ERROR}
    return {"ok": True, "imported": len(posted)}
