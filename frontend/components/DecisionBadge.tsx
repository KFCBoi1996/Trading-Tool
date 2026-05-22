export function DecisionBadge({ decision }: { decision: string }) {
  const good = decision.includes('RECOMMENDATION');
  const watch = decision.includes('WATCHLIST');
  const cls = good ? 'border-emerald-500 text-emerald-200' : watch ? 'border-sky-500 text-sky-200' : 'border-rose-500 text-rose-200';
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${cls}`}>{decision.replaceAll('_', ' ')}</span>;
}
