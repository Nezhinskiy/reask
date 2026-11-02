"""GET /catalog/{category}: the category page of the dealer portal."""

from catalog import pim_client, pricing, stock
from catalog.auth import dealer_from


def category_page(request, category):
    dealer = dealer_from(request)  # 401 if the token is missing or expired
    cards = pim_client.fetch_category(category)  # CAT-57: most of the morning p95 is here
    available = stock.available_m2([card["sku"] for card in cards])  # one query on `stock`
    return {
        "category": category,
        "items": [
            {
                "sku": card["sku"],
                "name": card["name"],
                "photo": card["photo_url"],
                "price": pricing.price_for(dealer, card),
                "in_stock_m2": available.get(card["sku"], 0),
            }
            for card in cards
        ],
    }
