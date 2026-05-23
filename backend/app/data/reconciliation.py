from __future__ import annotations

from app.schemas import ProviderReconciliationOut


class ProviderReconciliationEngine:
    def reconcile(self, instrument: str, timeframe: str, providers_checked: list[str], data_status: str) -> ProviderReconciliationOut:
        if not providers_checked:
            return ProviderReconciliationOut(
                instrument=instrument,
                timeframe=timeframe,
                status="UNAVAILABLE",
                data_status="UNAVAILABLE",
                providers_checked=[],
                max_price_disagreement=None,
                tolerance=None,
                rejection_reason="No market providers available",
            )
        return ProviderReconciliationOut(
            instrument=instrument,
            timeframe=timeframe,
            status="SINGLE_PROVIDER",
            data_status=data_status,  # type: ignore[arg-type]
            providers_checked=providers_checked,
            max_price_disagreement=None,
            tolerance=None,
            rejection_reason="Only one provider configured; cross-provider disagreement cannot be tested",
        )
