# OPS-140 cutover runbook

Owner: the on-call engineer for the window.

Both sites use the same managed Postgres (`pg-main`) and the same object storage, so no data is
copied: only the place that serves requests changes.

1. 21:45 Freeze deploys on both sites.
2. 21:50 Scale `stagelark-api` on k-east to 6 replicas; check `/healthz` through 198.51.100.24.
3. 22:00 In the DNS provider's console, change the A record of `api.stagelark.example` from
   203.0.113.10 (old-dc's HAProxy) to 198.51.100.24 (k-east's ingress).
4. 22:00 to 22:30 Watch the error rate and p95 on k-east; requests on old-dc should fall to zero.
5. Rollback, if k-east's error rate is above 1% or its p95 above 300 ms for 5 minutes: change the
   A record back to 203.0.113.10. old-dc keeps running untouched until OPS-141, so the rollback
   is immediate.
6. 23:00 Close the window on the status page.
