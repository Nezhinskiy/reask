# Open tickets

## INGEST-31: kedr-pos files fail to parse every night

kedr-pos moved its cafés to a new export on 2026-10-30. Since the run of 2026-10-31 every
kedr-pos file fails to parse; the scheduler retries the whole run five times and then marks it
failed. Partners after kedr-pos in the run order (lumen-pos) are not loaded at all on those
nights. Cafés on kedr-pos and lumen-pos have had no stamps credited since Oct 30, and two chains
have already written to support.
