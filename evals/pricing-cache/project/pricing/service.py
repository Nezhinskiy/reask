from pricing import pricing_api


def get_price(sku: str, locale: str) -> dict:
    """Price for a product page. locale is e.g. "de-DE"; we ship 40 locales (see locales.txt)."""
    return pricing_api.get_price(sku=sku, locale=locale)
