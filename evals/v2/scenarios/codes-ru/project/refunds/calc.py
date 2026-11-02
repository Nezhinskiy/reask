"""Partial refunds (ORD-214): which items may be returned and how much goes back."""

from datetime import timedelta

RETURN_WINDOW = timedelta(days=14)  # BR-2; TD-3: the admin app has its own copy
PLANTS_WINDOW = timedelta(hours=24)  # BR-4


def refundable_items(order, claim, now):
    out = []
    for item in claim.items:
        window = PLANTS_WINDOW if item.category == "plants" else RETURN_WINDOW
        if now - order.delivered_at > window:
            continue
        # BR-4 also needs a photo of the plant; the claim form already uploads it to
        # claim.photo_ids, but nothing checks it yet.
        out.append(item)
    return out


def refund_amount(order, items):
    amount = sum(item.price * item.qty for item in items)
    if len(items) == len(order.items) and not order.handed_to_courier:
        amount += order.delivery_fee  # BR-6
    return amount
