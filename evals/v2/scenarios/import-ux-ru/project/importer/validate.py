"""Checks for one row of a bank statement before it becomes a ledger entry."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

CONTRACT = re.compile(r"\bдог(?:овор)?\.?\s*№?\s*(\d{3,6})", re.IGNORECASE)


class RowError(ValueError):
    pass


def validate_row(school, row):
    try:
        day = datetime.strptime(row["Дата"], "%d.%m.%Y").date()
    except ValueError:
        raise RowError("дата не в формате ДД.ММ.ГГГГ")
    try:
        amount = Decimal(row["Сумма"].replace(" ", "").replace(",", "."))
    except InvalidOperation:
        raise RowError("сумма не число")
    family = school.find_family(payer=row["Плательщик"], contract=_contract(row["Назначение"]))
    if family is None:
        raise RowError("плательщик не найден среди семей школы")
    return {"family_id": family.id, "date": day, "amount": amount}


def _contract(purpose):
    match = CONTRACT.search(purpose or "")
    return match.group(1) if match else None
