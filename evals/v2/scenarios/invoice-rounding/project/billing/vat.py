"""VAT on an invoice. Ardenian standard rate, 20%."""

from decimal import ROUND_HALF_UP, Decimal

from billing.models import Invoice, Line

VAT_RATE = Decimal("0.20")
CENT = Decimal("0.01")


def line_vat(line: Line) -> Decimal:
    return (line.net * VAT_RATE).quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_vat(invoice: Invoice) -> Decimal:
    # Each line rounded to 0.01, then summed. Vitrina rounds once on the order total (BILL-217).
    return sum((line_vat(line) for line in invoice.lines), Decimal("0"))


def invoice_total(invoice: Invoice) -> Decimal:
    return invoice.net + invoice_vat(invoice)
