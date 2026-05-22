import { DecisionBadge } from '../../../components/DecisionBadge';
import { getRecommendation } from '../../../lib/api';

export default async function SignalDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const recommendation = await getRecommendation('EUR_USD');
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-sky-300">Signal detail</p>
        <h1 className="mt-2 text-4xl font-bold">{id}</h1>
      </div>
      <section className="rounded-2xl border border-borderline bg-panel p-5">
        <div className="flex items-center justify-between"><h2 className="text-2xl font-semibold">Decision</h2><DecisionBadge decision={recommendation.final_arbiter.final_decision} /></div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Block title="Score breakdown" items={Object.entries(recommendation.ranking.score_breakdown).map(([k, v]) => `${k}: ${v.toFixed(1)}`)} />
          <Block title="Risk plan" items={[`Entry: ${recommendation.risk_plan.entry_low ?? 'n/a'} - ${recommendation.risk_plan.entry_high ?? 'n/a'}`, `SL: ${recommendation.risk_plan.stop_loss ?? 'n/a'}`, `TP1: ${recommendation.risk_plan.tp1 ?? 'n/a'}`, `TP2: ${recommendation.risk_plan.tp2 ?? 'n/a'}`, `RR: ${recommendation.risk_plan.rr_to_tp1 ?? 'n/a'}`]} />
          <Block title="Why take" items={recommendation.ai_analysis.why_take.map((i) => `${i.text} (${i.evidence_ids.join(', ')})`)} />
          <Block title="Why not take" items={recommendation.ai_analysis.why_not_take.map((i) => `${i.text} (${i.evidence_ids.join(', ')})`)} />
          <Block title="Evidence IDs" items={recommendation.strategy_signal.evidence.map((e) => `${e.evidence_id}: ${e.text}`)} />
          <Block title="Risk reviewer" items={[`Passed: ${recommendation.risk_review.risk_review_passed}`, ...(recommendation.risk_review.warnings || [])]} />
        </div>
      </section>
    </div>
  );
}

function Block({ title, items }: { title: string; items: string[] }) {
  return <div className="rounded-xl bg-black/25 p-4"><h3 className="font-semibold">{title}</h3><ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">{items.length ? items.map((item) => <li key={item}>{item}</li>) : <li>Unavailable</li>}</ul></div>;
}
