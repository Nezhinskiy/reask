"""Client for the PIM's HTTP API, run by the content team.

The content team edits cards (names, photos, base prices) in the PIM during the working day. The
PIM sends no change notifications: no webhook, no feed, only GET.
"""

import os

import httpx

PIM_URL = os.environ["PIM_URL"]


def fetch_category(category):
    # One call returns every card in the category (60 to 400 cards, about 2 KB each).
    response = httpx.get(f"{PIM_URL}/v2/categories/{category}/cards", timeout=5.0)
    response.raise_for_status()
    return response.json()["cards"]
