import { DataStatusBanner } from '../../components/DataStatusBanner';
import { SignalCard } from '../../components/SignalCard';
import { getHealth, getRecommendation, instruments } from '../../lib/api';

export default async function DashboardPage() {
  const [health, ...recommendations] = await Promise.all([getHealth(), ...instruments.map((instrument) => getRecommendation(instrument))]);
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-sky-300">Decision-support only</p>
        <h1 className="mt-2 text-4xl font-bold">Signal Intelligence Dashboard</h1>
        <p className="mt-3 max-w-3xl text-slate-300">Scans selected FX pairs, ranks deterministic setups, blocks unsafe recommendations, and journals final decisions. No broker execution or trade buttons exist.</p>
      </div>
      <DataStatusBanner status={health.mock_data_enabled ? 'MOCK' : 'LIVE'} provider="backend config" reason={health.mock_data_enabled ? 'MOCK_DATA is enabled. Live trade recommendations are blocked.' : null} />
      <div className="grid gap-5 lg:grid-cols-2">
        {recommendations.map((recommendation) => <SignalCard key={recommendation.instrument} recommendation={recommendation} />)}
      </div>
      <section className="rounded-2xl border border-borderline bg-panel p-5">
        <h2 className="text-xl font-semibold">Feature flags</h2>
        <div className="mt-4 grid gap-2 md:grid-cols-3">
          {Object.entries(health.feature_flags).map(([flag, enabled]) => <div key={flag} className="rounded-xl bg-black/25 p-3 text-sm"><span className={enabled ? 'text-emerald-300' : 'text-slate-500'}>{enabled ? 'ON' : 'OFF'}</span> {flag}</div>)}
        </div>
      </section>
    </div>
  );
}
