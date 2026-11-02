# Semantic search (MOSS-311): product notes

**Goal.** When a customer types into the help-center search box, show the articles that match
what they mean, not just the words they typed.

- Results refresh as the customer types. The search call needs p95 at or under 150 ms.
- Each tenant searches only its own articles.
- Launch: the December release.
- Growth: the Enterprise tier opens in Q1. Sales expects "a few large tenants" with big help
  centers of their own; no sizes yet.
- Out of scope: searching tickets, reranking, answers generated from articles.
