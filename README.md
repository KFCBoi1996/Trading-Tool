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
