# ADR-7: Retire the legacy checkout service (accepted 2026-09-12)

Checkout v1 is retired by Dec 15; all traffic moves to checkout v2, which keeps sessions in
Postgres, not Redis. 6 dev-days left. After ADR-7 lands, only the admin panel uses the Redis
session store.
