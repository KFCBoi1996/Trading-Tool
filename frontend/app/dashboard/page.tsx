import { DataStatusBanner } from '../../components/DataStatusBanner';
import { MarketBrowser } from '../../components/MarketBrowser';
import { SignalCard } from '../../components/SignalCard';
import { getHealth, getRecommendation, instruments } from '../../lib/api';

export default async function DashboardPage() {
  const [health, ...recommendations] = await Promise.all([getHealth(), ...instruments.map((instrument) => getRecommendation(instrument))]);
  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_20%_20%,rgba(14,165,233,0.28),transparent_30rem),linear-gradient(135deg,#111827,#030712)] p-8 shadow-2xl shadow-black/30 md:p-12">
        <div className="absolute right-10 top-10 h-48 w-48 rounded-full bg-indigo-500/20 blur-3xl" />
        <div className="relative max-w-5xl">
          <p className="text-sm font-bold uppercase tracking-[0.35em] text-sky-300">Decision-support only</p>
          <h1 className="mt-4 text-5xl font-black leading-[0.9] tracking-[-0.08em] md:text-7xl">Signal Intelligence Dashboard</h1>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-300">
            Apple-inspired market command center for browsing ticker pages, extracting symbols, and
            pairing live quote intelligence with deterministic FX recommendations.
          </p>
        </div>
      </div>
      <MarketBrowser />
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
