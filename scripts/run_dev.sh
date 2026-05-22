#!/usr/bin/env bash
set -euo pipefail
pip install -e .[dev]
uvicorn trading_tool.api.app:app --reload --host 0.0.0.0 --port 8000
