# FX Signal Intelligence

A production-grade forex signal intelligence and decision-support service with an integrated market intelligence dashboard ("SignalGlass"). The app scans selected FX pairs, computes deterministic technical features, evaluates plugin strategies, checks regime/news/spread/data quality, ranks setups, builds a risk plan, runs a rules-only AI-compatible review path, passes every output through a final arbiter, journals decisions, and writes append-only audit records.

This app does **not** place trades, execute orders, connect to broker execution endpoints, store broker execution credentials, or claim guaranteed performance.

> This app is a decision-support and research tool only. It does not execute trades. Forex trading involves substantial risk. No output is guaranteed.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md), [`SECURITY.md`](./SECURITY.md), and [`docs/DEPLOYMENT_CHECKLIST.md`](./docs/DEPLOYMENT_CHECKLIST.md) for engineering practices and the live-deploy gate.

## Features

### Backend (`backend/`)
- FastAPI with lifespan startup, structured JSON logging, per-request IDs, stable error envelope.
- 12 deterministic strategy plugins, regime/news/risk/ranking engines, AI provider abstraction.
- Final Arbiter gates every decision; hard rules override AI; mock data blocks live recommendations.
- Append-only `recommendation_audit_log` stores the full serialized recommendation.
- `OutcomeTracker` walks stored candles to mark TP1/TP2/SL/expired outcomes; honest about ambiguous candles.
- `POST /api/scan` produces; `GET /api/recommendations/{instrument}` reads from the cached audit log within 15 minutes, falls back to scanning when stale.
- Ruff lint, pytest (27+ tests), Alembic migration baseline.

### Frontend (`frontend/`)
- Next.js + Tailwind dashboard with the SignalGlass UI language.
- Built-in **MarketBrowser** with URL-to-ticker detection, sample tickers, and live quote sparkline via the proxy at `/api/market/quote`.
- FX recommendation cards, pair detail with TradingView Lightweight Charts (entry/SL/TP/TP2 price lines drawn only when the risk engine produced them), signal detail, journal, settings, admin health pages.
- Precision-aware price formatting (5 dp for majors, 3 dp for JPY pairs), scan trigger button, structured error UI surfacing backend `request_id`.
- ESLint flat config + TypeScript strict, all CI checks green.

### Worker (`workers/`)
- Real jobs for `candle_sync`, `quote_sync`, `calendar_sync`, `news_sync`, `signal_scan`, `outcome_tracking`, and `health_heartbeat`, all writing `system_health_events` per run.

### Infra
- Non-root Dockerfiles with HEALTHCHECKs (backend, worker, frontend).
- Docker Compose with Postgres/Redis healthchecks.
- `render.yaml` with `healthCheckPath`, the standalone Next.js server, and cron jobs for candle sync, signal scan, outcome tracking, and heartbeat.
- CI: backend Ruff + Alembic + pytest; frontend ESLint + type-check + build.

## Module architecture

- **Data providers** (`backend/app/data/`): forex, calendar, news interfaces + deterministic mock + provider reconciliation.
- **Feature engine** (`backend/app/features/`): EMA/SMA/RSI/MACD/ATR/ADX/Bollinger/Donchian + structure/session/volatility/spread features.
- **Strategy engine** (`backend/app/strategies/`): 12 plugin classes with versioned `strategy_id`/`strategy_version` and required `evidence_id`s.
- **Regime engine** (`backend/app/regime/`): trend/range/volatility/session classifier with preferred/blocked strategy mapping.
- **News engine** (`backend/app/news/`): blackout/caution windows from calendar events.
- **Ranking engine** (`backend/app/ranking/`): weighted score with hard overrides.
- **Risk engine** (`backend/app/risk/`): entry/SL/TP1/TP2, RR, invalidation, validity window, missed-entry detection.
- **AI layer** (`backend/app/ai/`): provider abstraction with rules-only structured JSON stub; AI cannot create numeric trade levels or override hard risk rules.
- **Final Arbiter** (`backend/app/arbiter/`): only module allowed to set the display mode; respects mock-data and paper-validation flags.
- **Journal + audit** (`backend/app/journal/`, `backend/app/audit/`): persists signals, plans, rankings, and writes append-only audit rows.
- **Observability** (`backend/app/observability/`): structured logging, request middleware, error handlers.

## Database

Alembic baseline creates: `instruments`, `candles`, `quotes`, `economic_events`, `news_items`, `strategy_definitions`, `strategy_signals`, `regime_snapshots`, `ranked_setups`, `trade_plans`, `ai_reviews`, `signal_outcomes`, `users`, `watchlists`, `alerts`, `recommendation_audit_log`, `system_health_events`, `feature_flags`.

Indexed for the most common queries (candles by instrument/timeframe/timestamp, audit by signal/created_at/decision, outcomes by signal, etc.). Candle/quote tables are normal PostgreSQL and can later move to TimescaleDB hypertables.

## API surface

Health:
- `GET /api/health`
- `GET /api/admin/health`

Market:
- `GET /api/instruments`
- `GET /api/candles/{instrument}?timeframe=M15`
- `GET /api/quotes/{instrument}`
- `GET /api/spread/{instrument}`
- `GET /api/data-status/{instrument}`

Signals & recommendations:
- `POST /api/scan` and `POST /api/scan/{instrument}`
- `GET /api/signals`, `/api/signals/top`, `/api/signals/rejected`, `/api/signals/{signal_id}`
- `GET /api/recommendations/{instrument}` (cached when fresh, scan otherwise)
- `GET /api/recommendations/signal/{signal_id}`
- `GET /api/trade-plans/{signal_id}`

News, backtesting, journal, audit, alerts, feature flags:
- `GET /api/calendar/{instrument}`, `/api/news/{instrument}`, `/api/news-risk/{instrument}`
- `POST /api/backtest/run`, `GET /api/backtest/results`, `GET /api/backtest/summary/{strategy_id}`
- `GET /api/journal`, `/api/journal/stats`, `POST /api/journal/outcome/update`, `POST /api/journal/outcome/track`
- `GET /api/audit/{signal_id}`
- `POST /api/alerts` (only when Final Arbiter allows), `GET /api/alerts`, `DELETE /api/alerts/{alert_id}`
- `GET /api/feature-flags`, `PATCH /api/feature-flags/{flag_name}`

Frontend market proxy:
- `GET /api/market/quote?symbol=...` (Yahoo Finance-style intraday data)
- `GET /api/market/resolve?value=...`

## Local setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Then open [http://localhost:3000](http://localhost:3000).

### Worker
```bash
PYTHONPATH=backend python workers/main.py signal_scan
```
Available jobs: `candle_sync`, `quote_sync`, `calendar_sync`, `news_sync`, `signal_scan`, `outcome_tracking`, `provider_reconciliation`, `backtest_refresh`, `health_heartbeat`.

### Docker Compose
```bash
cp .env.example .env
docker compose up --build
```

## Render deployment

Use `render.yaml` from the repo root. It defines the backend, frontend (standalone Next.js server), worker, cron jobs (candle sync, signal scan, outcome tracking, heartbeat), and PostgreSQL database. See [`docs/DEPLOYMENT_CHECKLIST.md`](./docs/DEPLOYMENT_CHECKLIST.md) for the go-live gate.

Required environment variables (see `backend/.env.example`):

```
DATABASE_URL
REDIS_URL                # optional
FOREX_DATA_PROVIDER / FOREX_API_KEY
CALENDAR_DATA_PROVIDER / CALENDAR_API_KEY
NEWS_DATA_PROVIDER / NEWS_API_KEY
OPENAI_API_KEY or LLM_API_KEY
MOCK_DATA_ENABLED
LIVE_RECOMMENDATIONS_ENABLED
PAPER_VALIDATION_MODE_ENABLED
ALLOW_DELAYED_RECOMMENDATIONS
CORS_ORIGINS
```

## Verify

```bash
cd backend && ruff check . && DATABASE_URL=sqlite+pysqlite:///:memory: pytest
```

```bash
cd frontend && npm run lint && npm run type-check && npm run build
```

## Known limitations

- Real provider adapters are stubs (`backend/app/data/provider_interfaces.py::RealProviderStub`); they must be implemented before flipping `LIVE_RECOMMENDATIONS_ENABLED=true`.
- Redis queue integration is scaffolded; the worker currently runs jobs synchronously when invoked.
- Backtesting returns "Backtest unavailable" until historical stored candles and strategy replay logic are connected.
- AI uses a rules-only structured stub unless an LLM provider adapter is added.
- Alerts are recorded in-app only; an external notification channel must be added before production use.
