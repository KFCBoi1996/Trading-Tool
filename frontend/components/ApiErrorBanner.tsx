import type { ApiError } from '../lib/api';

export function ApiErrorBanner({ error }: { error: ApiError | null }) {
  if (!error) return null;
  return (
    <div className="rounded-xl border border-rose-700 bg-rose-950/60 p-4 text-sm">
      <p className="font-semibold text-rose-200">Backend request failed ({error.status || 'network'})</p>
      <p className="mt-1 text-rose-100">{error.message}</p>
      {error.requestId && <p className="mt-1 text-xs text-rose-300">request_id: {error.requestId}</p>}
    </div>
  );
}
