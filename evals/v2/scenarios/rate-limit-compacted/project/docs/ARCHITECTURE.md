# Architecture

Internet → API gateway (Kong, run by the platform team) → `ledgerly-api` Service → API pods.

- The gateway terminates TLS and routes by path. Its plugins (auth, rate limiting, request size)
  are switched on per route by the platform team on request.
- API pods are stateless; state lives in Postgres.
- The shared Redis (`redis-shared`) backs the job queue in `worker/`. Other teams use it too.
