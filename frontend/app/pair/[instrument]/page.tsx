import { ChartPanel } from '../../../components/ChartPanel';
import { DataStatusBanner } from '../../../components/DataStatusBanner';
import { getCandles, getRecommendation, instruments } from '../../../lib/api';

export function generateStaticParams() {
  return instruments.map((instrument) => ({ instrument }));
}

export default async function PairPage({ params }: { params: Promise<{ instrument: string }> }) {
  const { instrument } = await params;
  const [recommendation, candles] = await Promise.all([getRecommendation(instrument), getCandles(instrument, 'M15')]);
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-sky-300">Pair detail</p>
        <h1 className="mt-2 text-4xl font-bold">{instrument}</h1>
      </div>
      <DataStatusBanner status={recommendation.data_status} provider={recommendation.data_provider} reason={recommendation.data_quality_rejection_reason} />
      <ChartPanel candles={candles} recommendation={recommendation} />
      <div className="grid gap-5 lg:grid-cols-3">
        <Panel title="Regime"><p>Trend: {recommendation.regime.trend_state}</p><p>Strength: {recommendation.regime.trend_strength.toFixed(1)}</p><p>Volatility: {recommendation.regime.volatility_state}</p></Panel>
        <Panel title="News/calendar"><p>Status: {recommendation.news_risk.news_risk_status}</p><p>Blackout: {recommendation.news_risk.blackout_active ? 'yes' : 'no'}</p></Panel>
        <Panel title="Data quality"><p>Passed: {recommendation.data_quality_passed ? 'yes' : 'no'}</p><p>{recommendation.data_quality_rejection_reason || 'No rejection reason.'}</p></Panel>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-2xl border border-borderline bg-panel p-5"><h2 className="text-lg font-semibold">{title}</h2><div className="mt-3 space-y-2 text-sm text-slate-300">{children}</div></section>;
}
