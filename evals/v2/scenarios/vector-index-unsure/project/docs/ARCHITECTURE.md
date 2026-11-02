# Architecture

Mossline is a support desk: support agents answer tickets, customers read each tenant's help
center.

Browser → ingress → `mossline-api` (4 pods, Python) → Postgres.

- Postgres 14, one primary and one read replica, run by the data team. It holds tickets,
  articles, `chunk_vectors`, and the reporting schema the data team's dashboards read. Schema
  changes and extensions go through the data team's review.
- Help-center search today is Postgres full-text search on `articles.tsv`; see
  search/keyword.py.
- Embeddings come from embed-m2, the hosted embedding API we already pay for (768 dimensions).
