import { ApiErrorBanner } from '../../../components/ApiErrorBanner';
import { DecisionBadge } from '../../../components/DecisionBadge';
import { formatPrice, getRecommendationBySignal } from '../../../lib/api';

interface AuditRow {
  id?: string;
  signal_id?: string;
  instrument?: string;
  final_decision?: string;
  rejection_reason?: string | null;
  data_status?: string;
  data_provider?: string;
  score_breakdown?: Record<string, number>;
  risk_plan?: Record<string, unknown>;
  news_risk?: Record<string, unknown>;
  regime_snapshot?: Record<string, unknown>;
  ai_review?: Record<string, unknown>;
  risk_review?: Record<string, unknown>;
  input_payload?: Record<string, unknown>;
  output_payload?: Record<string, unknown>;
}

export default async function SignalDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { data, error } = await getRecommendationBySignal(id);
  const audit = data as AuditRow;
  const decision = audit.final_decision || 'UNAVAILABLE';
  const instrument = audit.instrument || 'EUR_USD';
  const breakdown = audit.score_breakdown || {};
  const plan = (audit.risk_plan as Record<string, number | string | null>) || {};
  const aiReview = (audit.ai_review as Record<string, unknown>) || {};
  const riskReview = (audit.risk_review as Record<string, unknown>) || {};
  const strategy = ((audit.input_payload as Record<string, unknown>)?.strategy_signal as Record<string, unknown>) || {};
  const evidence = (strategy?.evidence as Array<{ evidence_id: string; text: string }>) || [];
  const whyTake = (aiReview?.why_take as Array<{ text: string; evidence_ids: string[] }>) || [];
  const whyNotTake = (aiReview?.why_not_take as Array<{ text: string; evidence_ids: string[] }>) || [];
  const warnings = (riskReview?.warnings as string[]) || [];
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-sky-300">Signal detail</p>
        <h1 className="mt-2 text-4xl font-bold">{id}</h1>
      </div>
      <ApiErrorBanner error={error} />
      <section className="rounded-2xl border border-borderline bg-panel p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">Decision</h2>
          <DecisionBadge decision={decision} />
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Block
            title="Score breakdown"
            items={Object.entries(breakdown).map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(1) : String(v)}`)}
          />
          <Block
            title="Risk plan"
            items={[
              `Entry: ${formatPrice(plan.entry_low as number | null, instrument)} - ${formatPrice(plan.entry_high as number | null, instrument)}`,
              `SL: ${formatPrice(plan.stop_loss as number | null, instrument)}`,
              `TP1: ${formatPrice(plan.tp1 as number | null, instrument)}`,
              `TP2: ${formatPrice(plan.tp2 as number | null, instrument)}`,
              `RR TP1: ${plan.rr_to_tp1 ?? 'n/a'}`,
              `RR TP2: ${plan.rr_to_tp2 ?? 'n/a'}`
            ]}
          />
          <Block title="Why take" items={whyTake.map((i) => `${i.text} (${i.evidence_ids.join(', ')})`)} />
          <Block title="Why not take" items={whyNotTake.map((i) => `${i.text} (${i.evidence_ids.join(', ')})`)} />
          <Block title="Evidence IDs" items={evidence.map((e) => `${e.evidence_id}: ${e.text}`)} />
          <Block title="Risk reviewer" items={[`Passed: ${riskReview.risk_review_passed ?? 'unknown'}`, ...warnings]} />
        </div>
      </section>
    </div>
  );
}

function Block({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl bg-black/25 p-4">
      <h3 className="font-semibold">{title}</h3>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
        {items.length ? items.map((item) => <li key={item}>{item}</li>) : <li>Unavailable</li>}
      </ul>
    </div>
  );
}
