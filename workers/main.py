from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from app.constants import SUPPORTED_INSTRUMENTS, SUPPORTED_TIMEFRAMES
from app.data.mock_provider import DeterministicMockMarketProvider
from app.db.init_db import create_db_and_tables, seed_reference_data
from app.db.models import SystemHealthEvent
from app.db.session import SessionLocal
from app.journal.outcomes import OutcomeTracker
from app.journal.service import SignalJournalService
from app.observability import configure_logging, get_logger

log = get_logger("worker")

JOBS = {
    "candle_sync": "Sync M15/H1/H4 candles for active pairs",
    "quote_sync": "Sync latest quote/spread snapshots",
    "calendar_sync": "Sync economic calendar risk windows",
    "news_sync": "Sync news summaries",
    "provider_reconciliation": "Compare configured providers",
    "signal_scan": "Run full feature/strategy/ranking/risk/AI/arbiter pipeline",
    "outcome_tracking": "Update open signal outcomes from stored candles",
    "backtest_refresh": "Refresh backtest summaries when enough stored candle history exists",
    "health_heartbeat": "Write worker heartbeat status to system_health_events",
}


def _record_event(db, *, service: str, event_type: str, status: str, message: str, metadata: dict) -> None:
    db.add(
        SystemHealthEvent(
            service_name=service,
            event_type=event_type,
            status=status,
            message=message,
            metadata_json=metadata,
        )
    )
    db.commit()


def run_job(job: str) -> dict:
    if job not in JOBS:
        raise ValueError(f"Unknown job: {job}")
    configure_logging()
    create_db_and_tables()
    db = SessionLocal()
    try:
        seed_reference_data(db)
        service = SignalJournalService()
        provider = DeterministicMockMarketProvider()
        if job == "candle_sync":
            total = 0
            for instrument in SUPPORTED_INSTRUMENTS:
                for timeframe in SUPPORTED_TIMEFRAMES:
                    candles = provider.get_latest_candles(instrument, timeframe, 240)
                    total += service.persist_candles(db, candles)
            return _result(db, job, "ok", f"Synced {total} candle rows", {"persisted": total})
        if job == "quote_sync":
            for instrument in SUPPORTED_INSTRUMENTS:
                service.persist_quote(db, provider.get_latest_quote(instrument))
            return _result(db, job, "ok", "Quote sync complete", {"instruments": list(SUPPORTED_INSTRUMENTS)})
        if job in {"calendar_sync", "news_sync"}:
            counts = {}
            for instrument in SUPPORTED_INSTRUMENTS:
                counts[instrument] = service.persist_news_and_events(db, instrument)
            return _result(db, job, "ok", f"{job} complete", {"counts": counts})
        if job == "signal_scan":
            results = service.scan_all(db)
            decisions = [r.final_arbiter.final_decision for r in results]
            return _result(db, job, "ok", "Signal scan complete", {"signals": len(results), "decisions": decisions})
        if job == "outcome_tracking":
            tracker = OutcomeTracker()
            outcome = tracker.track(db)
            return _result(db, job, "ok", "Outcome tracking complete", outcome)
        if job == "health_heartbeat":
            return _result(db, job, "ok", "Heartbeat written", {"timestamp": datetime.now(timezone.utc).isoformat()})
        return _result(db, job, "scaffolded", JOBS[job], {"note": "scaffolded job; implement adapter to enable"})
    finally:
        db.close()


def _result(db, job: str, status: str, message: str, metadata: dict) -> dict:
    _record_event(db, service="worker", event_type=job, status=status, message=message, metadata=metadata)
    log.info("worker_job_complete", extra={"job": job, "status": status, "metadata": metadata})
    return {"job": job, "status": status, "message": message, "metadata": metadata}


def main() -> None:
    parser = argparse.ArgumentParser(description="FX Signal Intelligence worker")
    parser.add_argument("job", choices=sorted(JOBS), nargs="?", default="signal_scan")
    args = parser.parse_args()
    result = run_job(args.job)
    print(json.dumps(result, default=str))
    sys.exit(0)


if __name__ == "__main__":
    main()
