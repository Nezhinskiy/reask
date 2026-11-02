"""Nightly (MOSS-298): chunk every article, embed the chunks with embed-m2, store them.

Vectors go to chunk_vectors as raw float32 bytes. Nothing reads them yet; MOSS-311 decides how
they are searched.
"""

import array

CHUNK_WORDS = 200
UPSERT = """
INSERT INTO chunk_vectors (article_id, tenant_id, n, vec) VALUES (%s, %s, %s, %s)
ON CONFLICT (article_id, n) DO UPDATE SET vec = EXCLUDED.vec
"""


def chunks(body: str) -> list[str]:
    words = body.split()
    return [" ".join(words[i:i + CHUNK_WORDS]) for i in range(0, len(words), CHUNK_WORDS)]


def run(db, embed_m2) -> None:
    for article in db.fetch("SELECT id, tenant_id, body FROM articles"):
        for n, text in enumerate(chunks(article.body)):
            vec = embed_m2(text)  # 768 floats
            db.execute(UPSERT, (article.id, article.tenant_id, n, array.array("f", vec).tobytes()))
