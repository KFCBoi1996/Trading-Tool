# FX Signal Intelligence MVP

A production-oriented MVP for forex signal intelligence and decision support. The app scans selected FX pairs, computes deterministic technical features, evaluates plugin strategies, checks regime/news/spread/data quality, ranks setups, builds a risk plan, runs a rules-only AI-compatible review path, passes every output through a final arbiter, journals decisions, and writes append-only audit records.

This app does **not** place trades, execute orders, connect to broker execution endpoints, store broker execution credentials, or claim guaranteed performance.

> This app is a decision-support and research tool only. It does not execute trades. Forex trading involves substantial risk. No output is guaranteed.

## Implementation plan

1. Establish the monorepo structure, FastAPI backend, Next.js frontend, worker, health checks, environment examples, CI, and Render deployment files.
2. Add PostgreSQL-compatible SQLAlchemy models and Alembic baseline migration for instruments, candles, quotes, events, news, strategies, signals, rankings, plans, AI reviews, outcomes, users, watchlists, alerts, audit log, health, and feature flags.
3. Add provider interfaces plus deterministic mock adapters. Mock data is labeled `MOCK_DATA`/`MOCK` and blocks user-facing live recommendations.
4. Implement deterministic feature, regime, strategy, news, ranking, risk, AI-review-stub, final arbiter, journal, audit, backtest-scaffold, alerts, and health modules.
5. Expose the required API endpoint surface.
6. Build frontend screens for dashboard, pair detail/chart, signal detail, strategy lab, journal, settings, and admin health.
7. Add worker jobs, CI, tests, Docker Compose, and Render deployment instructions.

## Repo structure

```text
backend/
  alembic/
  app/
    api/
    db/
    data/
    features/
    strategies/
    regime/
    news/
    ranking/
    risk/
    arbiter/
    ai/
    backtesting/
    journal/
    audit/
    health/
    alerts/
  tests/
frontend/
  app/dashboard/
  app/pair/[instrument]/
  app/signals/[id]/
  app/strategy-lab/
  app/journal/
  app/settings/
  app/admin/health/
  components/
  lib/
  types/
workers/
infra/
.github/workflows/
render.yaml
docker-compose.yml
```

## Module-by-module architecture

- **Data providers** (`backend/app/data`): Interface-based forex, calendar, and news providers. Real providers are explicit stubs until keys/adapters are configured. The deterministic mock provider returns reproducible candles/quotes/events/news and marks all outputs as mock.
- **Feature engine** (`backend/app/features`): Calculates EMA, SMA, RSI, MACD, ATR, ADX-style trend strength, Bollinger, Donchian, swings, support/resistance, session, volatility, spread, and derived status fields from candles/quotes.
- **Strategy engine** (`backend/app/strategies`): Plugin-style `BaseStrategy` with 12 MVP strategy classes. Strategies emit `StrategySignalOut` objects with evidence IDs and never produce final recommendations.
- **Regime engine** (`backend/app/regime`): Classifies trend/range/volatility/session context and preferred/blocked strategy families.
- **News/calendar engine** (`backend/app/news`): Applies blackout/caution logic from provider events and labels mock/unavailable data.
- **Provider reconciliation** (`backend/app/data/reconciliation.py`): Returns `SINGLE_PROVIDER` for MVP and is ready for multi-provider disagreement checks.
- **Correlation context** (`backend/app/data/correlation_context.py`): Scaffold that returns unavailable rather than inventing DXY/yield/commodity context.
- **Ranking engine** (`backend/app/ranking`): Transparent weighted scoring with hard overrides for data quality, mock/stale/degraded/unavailable data, news blackout, spread, reward/risk, missing levels, and missed entries.
- **Risk engine** (`backend/app/risk`): Calculates entry zone, stop, TP1/TP2, reward/risk, invalidation, validity window, spread cost, and missed-entry rejection.
- **AI layer** (`backend/app/ai`): LLM provider abstraction with a rules-only structured JSON stub. It summarizes only backend-provided values and cannot create prices, scores, or trade levels.
- **Final arbiter** (`backend/app/arbiter`): The only module allowed to set display mode. Hard rules override AI; mock data and paper validation block user-facing trade recommendations.
- **Journal/audit** (`backend/app/journal`, `backend/app/audit`): Saves signals/plans/rankings and writes append-only audit log rows for final decisions.
- **Backtesting** (`backend/app/backtesting`): Scaffold returns “Backtest unavailable” until actual stored candle samples are calculated; it makes no performance claims.
- **Frontend** (`frontend/`): Next.js app using Tailwind and TradingView Lightweight Charts with safety banners and no trade execution controls.
- **Workers** (`workers/`): Job entrypoint for sync, scan, reconciliation, outcome tracking, backtest refresh, and health heartbeat.

## Database schema summary

The Alembic baseline creates these tables: `instruments`, `candles`, `quotes`, `economic_events`, `news_items`, `strategy_definitions`, `strategy_signals`, `regime_snapshots`, `ranked_setups`, `trade_plans`, `ai_reviews`, `signal_outcomes`, `users`, `watchlists`, `alerts`, `recommendation_audit_log`, `system_health_events`, and `feature_flags`.

Required indexes are included for candles, quotes, economic events, news, strategy signals, ranked setups, trade plans, outcomes, and audit queries. Candle/quote schemas are normal PostgreSQL tables that can later migrate to TimescaleDB hypertables if needed.

## API endpoints

Health:
- `GET /api/health`
- `GET /api/admin/health`

Market:
- `GET /api/instruments`
- `GET /api/candles/{instrument}?timeframe=M15`
- `GET /api/quotes/{instrument}`
- `GET /api/spread/{instrument}`
- `GET /api/data-status/{instrument}`

Signals/recommendations:
- `POST /api/scan`
- `GET /api/signals`
- `GET /api/signals/top`
- `GET /api/signals/rejected`
- `GET /api/signals/{signal_id}`
- `GET /api/recommendations/{instrument}`
- `GET /api/recommendations/signal/{signal_id}`
- `GET /api/trade-plans/{signal_id}`

News/calendar:
- `GET /api/calendar/{instrument}`
- `GET /api/news/{instrument}`
- `GET /api/news-risk/{instrument}`

Backtesting:
- `POST /api/backtest/run`
- `GET /api/backtest/results`
- `GET /api/backtest/summary/{strategy_id}`

Journal/audit/alerts/flags:
- `GET /api/journal`
- `GET /api/journal/stats`
- `POST /api/journal/outcome/update`
- `GET /api/audit/{signal_id}`
- `POST /api/alerts`
- `GET /api/alerts`
- `DELETE /api/alerts/{alert_id}`
- `GET /api/feature-flags`
- `PATCH /api/feature-flags/{flag_name}`

## Local setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
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

### Worker

```bash
PYTHONPATH=backend python3 workers/main.py signal_scan
```

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

## Render deployment

Use `render.yaml` from the repo root. It defines:

- Backend web service: installs backend requirements, runs `alembic upgrade head`, starts FastAPI.
- Frontend web service: installs npm dependencies, builds Next.js, starts Next.
- Worker service: runs the worker scan entrypoint.
- Cron jobs: candle sync and signal scan placeholders.
- PostgreSQL database.

Set real provider keys and flip flags only after adapters are implemented and verified:

```text
FOREX_DATA_PROVIDER
FOREX_API_KEY
CALENDAR_DATA_PROVIDER
CALENDAR_API_KEY
NEWS_DATA_PROVIDER
NEWS_API_KEY
OPENAI_API_KEY or LLM_API_KEY
MOCK_DATA_ENABLED=false
LIVE_RECOMMENDATIONS_ENABLED=true
PAPER_VALIDATION_MODE_ENABLED=false
```

## Environment variables

See `.env.example`, `backend/.env.example`, and `frontend/.env.example`.

Important safety flags:

- `MOCK_DATA_ENABLED=true` labels all mock inputs and blocks live recommendations.
- `LIVE_RECOMMENDATIONS_ENABLED=false` prevents user-facing trade recommendations.
- `PAPER_VALIDATION_MODE_ENABLED=true` journals setups without showing them as live recommendations.

## Test and validation commands

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
pytest
```

```bash
cd frontend
npm install
npm run type-check
npm run build
```

CI runs backend tests, migration check, frontend type checks, and frontend build.

## Known assumptions

- No live market, calendar, news, or LLM API keys are configured by default.
- Deterministic mock providers are used for MVP operation and UI development.
- Mock data is explicitly labeled and blocks user-facing live recommendations.
- Backtest metrics are not claimed until calculated from actual stored candle data.
- Paper validation mode is enabled by default.

## Known limitations

- Real provider adapters are stubs and must be implemented for live data.
- Redis queue integration is scaffolded; the MVP worker runs jobs synchronously.
- Backtesting returns “Backtest unavailable” until historical stored candles and strategy replay logic are connected.
- AI uses a rules-only structured stub unless an LLM provider adapter is added.
- Frontend signal detail currently renders a recommendation-shaped detail view and can be extended to fetch an exact audit payload by signal ID.
- Alerts are scaffolded and require arbiter-approved creation wiring for production notifications.

## Mock/scaffolded features

Mock data:
- Candles, quotes/spreads, economic events, and news headlines from `DeterministicMockMarketProvider`.

Scaffolded for future expansion:
- Real data providers.
- Multi-provider reconciliation disagreement checks.
- Correlation context (DXY, yields, gold, oil, risk sentiment).
- Backtesting calculations and calibration buckets.
- Redis-backed queue processing.
- Email/notification alert delivery.
- Champion/challenger manual promotion workflow.

## Next-step roadmap

1. Implement real provider adapters and secure Render environment variables.
2. Replace rules-only LLM stub with a strict JSON LLM adapter and schema validation retry/fail-closed handling.
3. Add stored-candle backtest replay with lookahead-bias protections and outcome calibration buckets.
4. Expand outcome tracking to close open signals automatically from completed candles.
5. Add exact signal detail retrieval from audit payloads and richer chart overlays for support/resistance and strategy markers.
6. Add Redis-backed worker scheduling and alert delivery.
# Trading-Tool

Initial scaffold for a quant-oriented trading platform with a clean service architecture.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
uvicorn trading_tool.api.app:app --reload
```

## API

- `GET /health`
- `POST /v1/signals`

Example payload:

```json
{
  "symbol": "AAPL",
  "timeframe": "1D"
}
```

## Project Structure

- `src/trading_tool/api` - HTTP interfaces
- `src/trading_tool/core` - domain models
- `src/trading_tool/services` - strategy and orchestration services
- `docs` - architecture and design notes
- `infra` - local runtime/deployment bootstrap
