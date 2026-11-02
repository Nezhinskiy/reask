"""MIG-21: fill orders.total_minor from orders.total_text, one wave of order years at a time."""

import argparse
import time
from decimal import Decimal, InvalidOperation

from shop.db import connect

UPDATE = "UPDATE orders SET total_minor = %s WHERE id = %s AND total_minor IS NULL"


def to_minor(text: str) -> int | None:
    try:
        return int(Decimal(text.strip()) * 100)
    except InvalidOperation:
        return None  # 'N/A' and other unparseable totals stay NULL


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--years", help="e.g. 2019-2020")
    p.add_argument("--months", help="e.g. 2024-01..2024-06")
    p.add_argument("--batch-size", type=int, default=5000)
    p.add_argument("--throttle-ms", type=int, default=0)
    args = p.parse_args()
    db = connect()
    for batch in db.pending_orders(args.years, args.months, args.batch_size):
        db.executemany(UPDATE, [(to_minor(o.total_text), o.id) for o in batch])
        db.commit()
        time.sleep(args.throttle_ms / 1000)


if __name__ == "__main__":
    main()
