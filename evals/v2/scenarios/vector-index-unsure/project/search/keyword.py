"""Help-center search today: Postgres full-text search over one tenant's articles."""

QUERY = """
SELECT id, title
FROM articles
WHERE tenant_id = %(tenant)s AND tsv @@ websearch_to_tsquery('english', %(q)s)
ORDER BY ts_rank(tsv, websearch_to_tsquery('english', %(q)s)) DESC
LIMIT 10
"""


def search(db, tenant: int, q: str) -> list[tuple[int, str]]:
    return db.fetch(QUERY, {"tenant": tenant, "q": q})
