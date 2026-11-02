"""Client for the upstream pricing API.

The API returns {"amount": ..., "currency": ...}. Most SKUs have one EUR list price; the API
converts it with the daily rate table. Exceptions are SKUs with a country price set by
merchandising (COUNTRY_PRICES below mirrors the API's current data).
"""

COUNTRY_PRICES = {
    "B-2210": {"DE": 49.00, "AT": 45.00},
    "K-0915": {"FR": 129.00, "BE": 119.00},
    "T-3302": {"IT": 18.50, "ES": 16.90},
}


def get_price(sku: str, locale: str) -> dict:
    raise NotImplementedError("network call")
