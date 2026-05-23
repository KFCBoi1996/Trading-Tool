# Deployment checklist

Run through every item before allowing live recommendations.

## Pre-deploy

- [ ] Backend tests pass (`pytest`, `ruff check .`).
- [ ] Frontend lints, type-checks, and builds (`npm run lint && npm run type-check && npm run build`).
- [ ] `alembic upgrade head` completes against the target database.
- [ ] `.env` values match `backend/.env.example` keys.
- [ ] Real provider adapters (forex, calendar, news) are implemented and credentials are set.
- [ ] An LLM provider adapter has been wired in if AI analysis is enabled.
- [ ] Provider reconciliation tolerances are configured (when more than one provider is used).
- [ ] Spread thresholds in `backend/app/constants.py::PAIR_SPREAD_LIMIT_PIPS` reflect broker norms.

## Feature flags

| Flag | Production default | Notes |
| ---- | ------------------ | ----- |
| `MOCK_DATA_ENABLED` | `false` | Set to `true` only for staging or test |
| `LIVE_RECOMMENDATIONS_ENABLED` | `false` until validated | Flip to `true` only after staging validation |
| `PAPER_VALIDATION_MODE_ENABLED` | `true` until calibration data exists | Keeps user-facing recommendations off |
| `AI_ANALYST_ENABLED` | `true` if LLM key is set | Falls back to rules stub otherwise |
| `AI_RISK_REVIEWER_ENABLED` | `true` if LLM key is set | Falls back to rules stub otherwise |
| `ALERTS_ENABLED` | `true` after notification channel is configured | |

## Post-deploy verification

- [ ] `GET /api/health` returns `status=healthy` and `database=ok`.
- [ ] `POST /api/scan/EUR_USD` returns a journaled `RecommendationOut` and `audit_id` is set.
- [ ] `GET /api/recommendations/EUR_USD` returns a cached recommendation immediately after.
- [ ] `GET /api/admin/health` shows worker heartbeat events for `candle_sync`, `signal_scan`, and `outcome_tracking`.
- [ ] `GET /api/journal` shows recent decisions and rejected setups.
- [ ] Frontend dashboard renders all five pairs, banner shows `LIVE` (or the actual data status), and chart shows entry/SL/TP lines only when the risk engine produced them.
- [ ] Audit log entries reference the expected `strategy_version`, `ranking_version`, `risk_engine_version`, and `arbiter_version`.

## Rollback

- Render: revert the responsible service to a known-good commit and `alembic downgrade` if a destructive migration was applied.
- Local: `git revert` the offending commit and redeploy.

## Incident response

1. Set `LIVE_RECOMMENDATIONS_ENABLED=false` and `PAPER_VALIDATION_MODE_ENABLED=true`.
2. Snapshot the latest 100 rows of `recommendation_audit_log` and `system_health_events` for the incident report.
3. Identify the offending version (`strategy_version`, `ranking_version`, `risk_engine_version`, `arbiter_version`) from audit metadata.
4. Roll back the offending version.
5. Reproduce with the cached audit input payload before re-enabling live recommendations.
