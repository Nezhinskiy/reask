# partner-ingest

Nightly ingest of point-of-sale transactions for Tenthcup, a loyalty-stamp app for independent
cafés ("every tenth cup is on us"). Each POS partner drops one CSV per café chain per day on our
SFTP; `ingest/run.py` parses every file and upserts the rows into Postgres (`transactions`).
Stamps are credited to customers from that table at 06:00 UTC.

- Schedule and retries: `deploy/schedule.yaml` (runs at 02:00 UTC for the previous day).
- Partners and their file formats: `docs/PARTNERS.md`.
- Past incidents: `docs/INCIDENTS.md`.
- Run history: `ingestctl runs --job partner-ingest` (platform CLI).

Run one partner by hand:

    python -m ingest.run --date 2026-11-01 --partner lumen-pos
