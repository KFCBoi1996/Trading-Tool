from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("MOCK_DATA_ENABLED", "true")
os.environ.setdefault("LIVE_RECOMMENDATIONS_ENABLED", "false")
os.environ.setdefault("PAPER_VALIDATION_MODE_ENABLED", "true")
