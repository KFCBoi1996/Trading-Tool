from __future__ import annotations

import argparse
from app.db.init_db import create_db_and_tables, seed_reference_data
from app.db.session import SessionLocal
from app.journal.service import SignalJournalService

JOBS = {
    "candle_sync": "Sync deterministic/mock candles for active pairs",
    "quote_sync": "Sync latest quote/spread snapshots",
    "calendar_sync": "Sync economic calendar risk windows",
    "news_sync": "Sync news summaries",
    "provider_reconciliation": "Compare configured providers",
    "signal_scan": "Run feature, strategy, ranking, risk, AI review, arbiter, journal, and audit pipeline",
    "outcome_tracking": "Update open signal outcomes from stored candles",
    "backtest_refresh": "Refresh backtest summaries when enough stored candle history exists",
    "health_heartbeat": "Write worker heartbeat status",
}

def run_job(job: str) -> dict:
    create_db_and_tables()
    db = SessionLocal()
    try:
        seed_reference_data(db)
        service = SignalJournalService()
        if job == "signal_scan":
            results = service.scan_all(db)
            return {"job": job, "status": "ok", "signals": len(results), "decisions": [r.final_arbiter.final_decision for r in results]}
        return {"job": job, "status": "scaffolded", "description": JOBS[job]}
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FX Signal Intelligence worker")
    parser.add_argument("job", choices=sorted(JOBS), nargs="?", default="signal_scan")
    args = parser.parse_args()
    print(run_job(args.job))
