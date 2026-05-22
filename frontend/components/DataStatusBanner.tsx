import type { DataStatus } from '../types/api';

export function DataStatusBanner({ status, provider, reason }: { status: DataStatus; provider?: string; reason?: string | null }) {
  const safe = status === 'LIVE';
  return (
    <div className={`rounded-xl border p-4 ${safe ? 'border-emerald-700 bg-emerald-950/50' : 'border-amber-600 bg-amber-950/60'}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <strong>{safe ? 'LIVE data' : `${status} data warning`}</strong>
        <span className="rounded-full bg-black/30 px-3 py-1 text-xs">Provider: {provider || 'unknown'}</span>
      </div>
      {!safe && <p className="mt-2 text-sm text-amber-100">{reason || 'Non-live or degraded data blocks user-facing live recommendations. Mock data is labeled MOCK_DATA.'}</p>}
    </div>
  );
}
