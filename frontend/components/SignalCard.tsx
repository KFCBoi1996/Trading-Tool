import Link from 'next/link';
import { formatPrice } from '../lib/api';
import type { Recommendation } from '../types/api';
import { DecisionBadge } from './DecisionBadge';

export function SignalCard({ recommendation }: { recommendation: Recommendation }) {
  const plan = recommendation.risk_plan;
  const instrument = recommendation.instrument;
  return (
    <section className="rounded-2xl border border-borderline bg-panel p-5 shadow-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{instrument}</p>
          <h2 className="mt-1 text-2xl font-semibold">{recommendation.strategy_signal.strategy_id}</h2>
        </div>
        <DecisionBadge decision={recommendation.final_arbiter.final_decision} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <Metric label="Score" value={recommendation.ranking.final_score.toFixed(1)} />
        <Metric label="Direction" value={recommendation.strategy_signal.direction} />
        <Metric label="RR TP1" value={plan.rr_to_tp1 !== null ? plan.rr_to_tp1.toFixed(2) : 'n/a'} />
        <Metric label="News" value={recommendation.news_risk.news_risk_status} />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-400 md:grid-cols-4">
        <KV label="Entry" value={`${formatPrice(plan.entry_low, instrument)} – ${formatPrice(plan.entry_high, instrument)}`} />
        <KV label="Stop" value={formatPrice(plan.stop_loss, instrument)} />
        <KV label="TP1" value={formatPrice(plan.tp1, instrument)} />
        <KV label="TP2" value={formatPrice(plan.tp2, instrument)} />
      </div>
      {recommendation.final_arbiter.display_mode === 'no_trade' && (
        <div className="mt-4 rounded-xl border border-rose-900 bg-rose-950/40 p-3 text-sm">
          <strong>No Trade reasons</strong>
          <ul className="mt-2 list-disc pl-5 text-rose-100">
            {recommendation.no_trade_explanation.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="mt-4 flex gap-3 text-sm text-sky-300">
        <Link href={`/pair/${instrument}`}>Pair detail</Link>
        <Link href={`/signals/${recommendation.signal_id}`}>Signal detail</Link>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-black/25 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-black/15 px-2 py-1">
      <span className="text-slate-500">{label}:</span> <span className="text-slate-200">{value}</span>
    </div>
  );
}
