"""Dealer prices.

Every dealer sees their own price: the base price less their contract tier's discount, or a
personal price where one is agreed. Contract prices are confidential: dealers bid against each
other for the same building projects.
"""

TIER_DISCOUNT = {"A": 0.18, "B": 0.12, "C": 0.05}


def price_for(dealer, card):
    personal = dealer.contract_prices.get(card["sku"])
    if personal is not None:
        return personal
    return round(card["base_price"] * (1 - TIER_DISCOUNT[dealer.tier]), 2)
