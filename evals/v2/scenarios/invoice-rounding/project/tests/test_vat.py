from decimal import Decimal

from billing.models import Invoice, Line
from billing.vat import invoice_total, invoice_vat


def test_order_5532_from_bill_217():
    mug = Line("Кружка", 1, Decimal("10.03"))
    invoice = Invoice("S-5532", "Частный покупатель", None, [mug, mug, mug])
    assert invoice_vat(invoice) == Decimal("6.03")  # Vitrina showed 6.02
    assert invoice_total(invoice) == Decimal("36.12")  # Vitrina showed 36.11


def test_company_invoice():
    lines = [Line("Стул", 4, Decimal("1250.00")), Line("Стол", 1, Decimal("3999.99"))]
    invoice = Invoice("C-1180", "ООО «Пример»", "AR-4410-0093", lines)
    assert invoice_vat(invoice) == Decimal("1800.00")
