# Trading Tool Architecture (Scaffold)

## Layers
- **API Layer** (`src/trading_tool/api`): FastAPI endpoints.
- **Core Layer** (`src/trading_tool/core`): domain models and contracts.
- **Service Layer** (`src/trading_tool/services`): strategy logic and execution orchestration.

## Planned Extensions
- Broker adapters (IBKR/Alpaca/etc.)
- Market data ingestion + caching
- Backtest engine with vectorized simulation
- Risk management module (position sizing, drawdown controls)
- Front-end dashboard (React/Next.js)
- Deployment manifests (Docker + IaC)
