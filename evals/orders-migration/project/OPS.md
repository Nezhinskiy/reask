# Ops notes

- Postgres 15, primary + 1 replica. Deploys run migrations inside the deploy job, which times
  out after 10 minutes (DEPLOY-3).
- Replica lag alarm at 30 s. Last month a 6-minute table rewrite on `payments` paused writes
  and caused INC-212.
- `region` is needed by the tax report (TAX-19), due Dec 1. Reports may treat missing region as
  "unknown" until then.
