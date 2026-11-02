from api.store import invoices, payments


def create_invoice(request, key):
    return invoices.create(owner=key, body=request.json)


def get_invoice(request, key):
    return invoices.get(owner=key, invoice_id=request.params["id"])


def list_payments(request, key):
    return payments.list(owner=key, cursor=request.query.get("cursor"))
