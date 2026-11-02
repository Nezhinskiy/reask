# Pricing latency

Product pages wait ~800 ms on `pricing_api.get_price`. Plan agreed in standup (2026-10-20):
Redis, 10-minute TTL, in front of `get_price`. Owner: Dana. Must merge before the Nov 14 sale.

Open: what the cache key is. See PRICING-77.
