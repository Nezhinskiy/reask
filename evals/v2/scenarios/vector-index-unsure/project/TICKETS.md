# Open tickets

## MOSS-311: meaning-based help-center search

Customers search the help center in their own words and get nothing back: "can't log in" finds
no article, because the article is called "Resetting your password". Search should match the
meaning, not just the words. Product notes: docs/semantic-search-prd.md.

The vectors already exist (MOSS-298). Decide where and how they are searched, then build it.
Target: the December release.

## MOSS-298 (closed): nightly embedding job

Added search/embed_corpus.py. Every night it splits each article into chunks, embeds them with
embed-m2 and stores the vectors in the `chunk_vectors` table. Nothing reads them yet.
