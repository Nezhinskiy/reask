"""An invoice and its lines. Amounts are Decimal, net of VAT."""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Line:
    title: str
    qty: int
    unit_price: Decimal  # net of VAT

    @property
    def net(self) -> Decimal:
        return self.qty * self.unit_price


@dataclass
class Invoice:
    number: str
    buyer_name: str
    buyer_tax_id: str | None  # set for companies; None for private buyers from Vitrina
    lines: list[Line] = field(default_factory=list)

    @property
    def net(self) -> Decimal:
        return sum((line.net for line in self.lines), Decimal("0"))
