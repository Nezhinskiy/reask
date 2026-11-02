# Dealer portal: architecture

Written by the platform team, June 2026.

Dealer's browser → CDN (edge, run by the platform team; its config is in deploy/) → ingress →
`catalog-api` (4 pods) → its two sources:

- **PIM**, the product information system run by the content team: product cards (name, photos,
  size, packaging, base price). HTTP API, one call per category page.
- **Postgres `portal`**: dealers, their contract prices (`contract_prices`) and stock (`stock`).

Notes:

- Stock: the warehouse system pushes stock levels into `stock` every 5 minutes.
- Prices: every dealer has a contract tier (A, B or C) and may have personal prices for some
  items; see catalog/pricing.py.
- Every request carries the dealer's token in `Authorization`; `catalog-api` checks it.
- There is no shared cache today, and `catalog-api` pods keep no state between requests.
