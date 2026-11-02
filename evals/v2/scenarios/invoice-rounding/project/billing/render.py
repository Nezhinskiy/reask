"""The printed invoice: one row per line with its VAT (BILL-209), then the totals."""

from billing.models import Invoice
from billing.vat import invoice_total, invoice_vat, line_vat


def rows(invoice: Invoice) -> list[tuple[str, str, str]]:
    out = [(line.title, f"{line.net:.2f}", f"{line_vat(line):.2f}") for line in invoice.lines]
    out.append(("Итого НДС", "", f"{invoice_vat(invoice):.2f}"))
    out.append(("Итого к оплате", "", f"{invoice_total(invoice):.2f}"))
    return out
