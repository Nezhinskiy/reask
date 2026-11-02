"""Ledgerly public API: invoices and payments for partner integrations."""

from api.auth import api_key_from
from api.handlers import create_invoice, get_invoice, list_payments

ROUTES = {
    ("POST", "/v1/invoices"): create_invoice,
    ("GET", "/v1/invoices/{id}"): get_invoice,
    ("GET", "/v1/payments"): list_payments,
}


def handle(request):
    key = api_key_from(request)  # 401 if missing or revoked
    # API-88: the per-key limit goes here.
    return ROUTES[(request.method, request.route)](request, key)
