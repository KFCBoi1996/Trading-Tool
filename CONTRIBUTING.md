# Contributing

Thanks for your interest in improving the FX Signal Intelligence MVP.

## Principles

- This is a **decision-support tool only**. No code in this repository should be added to place trades, execute orders, connect to broker execution endpoints, or store broker execution credentials.
- The system fails closed. Hard risk gates (data quality, news blackout, spread, reward/risk, missing levels, missed entry, mock data) always override AI/ML output.
- Numeric trade levels and indicator values come from deterministic engines, not AI.
- Every decision must be journaled to `recommendation_audit_log`.

## Local development

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Lint and tests:

```bash
cd backend
ruff check .
DATABASE_URL=sqlite+pysqlite:///:memory: pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Lint, type-check, build:

```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

### Worker

```bash
PYTHONPATH=backend python workers/main.py signal_scan
```

Available jobs: `candle_sync`, `quote_sync`, `calendar_sync`, `news_sync`, `signal_scan`, `outcome_tracking`, `provider_reconciliation`, `backtest_refresh`, `health_heartbeat`.

## Adding a strategy

1. Add a class in `backend/app/strategies/plugins.py` extending `RuleStrategy`.
2. Set `strategy_id`, `strategy_version`, `family`, and `description`.
3. Register the class in `STRATEGIES`.
4. Bump `strategy_version` if you change behavior; never silently mutate existing logic.
5. Add tests covering at least: schema validity, evidence presence, and rejection behavior under bad inputs.

## Adding an API endpoint

1. Add the route in `backend/app/api/routes.py` under the appropriate `tags=` group.
2. Use a Pydantic `BaseModel` for request bodies.
3. Use `response_model` for typed responses where possible.
4. Add a corresponding `apiFetch` helper in `frontend/lib/api.ts` if the frontend needs it.
5. Add a backend test in `backend/tests/`.

## Commit hygiene

- One logical change per commit.
- Run `ruff check .` and `pytest` before pushing backend changes.
- Run `npm run lint && npm run type-check && npm run build` before pushing frontend changes.
- Reference any related issues or PRs in the body.

## Security

See [SECURITY.md](./SECURITY.md). Never commit secrets. Use environment variables and Render dashboard secrets.
