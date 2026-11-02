"""Payment gateway client (gateway API v2)."""

import os

import requests

GATEWAY_URL = os.environ["GATEWAY_URL"]
TIMEOUT_S = 10


def refund(payment_id, amount):
    # ORD-221: on a timeout this raises and the refund has to be repeated by hand.
    r = requests.post(
        f"{GATEWAY_URL}/v2/payments/{payment_id}/refunds",
        json={"amount": str(amount)},
        timeout=TIMEOUT_S,
    )
    r.raise_for_status()
    return r.json()["refund_id"]
