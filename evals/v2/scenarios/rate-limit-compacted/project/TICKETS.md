# Open tickets

## API-88: per-client rate limit on the public API

Each API key gets at most 100 requests per minute across all endpoints. Over the limit: HTTP 429
with a `Retry-After` header. Needed before the Nov 20 partner launch (Brightline goes live with
three integrations that day).

## INC-412 (closed): shared Redis saturated, 2026-10-14

Memory on the shared Redis hit its cap during the nightly export; the job queue stalled for
40 minutes and paged on-call twice. Follow-up: owners of new Redis keys must agree them with
on-call first.
