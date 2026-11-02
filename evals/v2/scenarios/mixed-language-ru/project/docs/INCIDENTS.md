# Incidents

## INC-7 (2026-08-19): store names mangled by encoding detection

To take files from new partners without per-partner setup, PR #212 decoded every file with
charset-normalizer's best guess instead of UTF-8. Partner files are short (one chain, 20–60 rows,
mostly digits plus a store name), and the guess was wrong for about one file in three: kedr-pos
pilot files written in Windows-1251 were read as cp1252, so «Кофейня на Садовой» was stored as
«Êîôåéíÿ íà Ñàäîâîé». Stamps went to a "new" café that did not exist for 9 days before finance
caught it at month end.

Fix: PR #212 reverted. Every file is read as UTF-8 again until a partner needs something else.

Lesson: do not guess an encoding from a file this short.
