from __future__ import annotations

from app.schemas import CorrelationContextOut, Evidence


class CorrelationContextEngine:
    def get_context(self, instrument: str) -> CorrelationContextOut:
        return CorrelationContextOut(
            instrument=instrument,
            status="unavailable",
            correlation_agreement="unavailable",
            summary="Correlation context is scaffolded but no DXY, yield, commodity, or cross-market provider is configured.",
            evidence=[Evidence(evidence_id=f"corr:{instrument}:unavailable", text="External correlation data unavailable; no context invented.", source="correlation_context")],
        )
