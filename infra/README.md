# Infrastructure notes

The MVP is deployable to Render with `render.yaml`:

- `fx-signal-backend`: FastAPI API service.
- `fx-signal-frontend`: Next.js frontend service.
- `fx-signal-worker`: worker service for scans/outcome jobs.
- `fx-candle-sync` and `fx-signal-scan`: cron jobs.
- `fx-signal-db`: PostgreSQL database.

Redis is represented in local Docker Compose and the environment contract. The MVP worker runs synchronously for deterministic validation; replacing it with a Redis-backed queue is isolated to `workers/` and the journal orchestration service.
