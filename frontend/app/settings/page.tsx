import { ApiErrorBanner } from '../../components/ApiErrorBanner';
import { getHealth, instruments } from '../../lib/api';

export default async function SettingsPage() {
  const { data: health, error } = await getHealth();
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-sky-300">Settings</p>
        <h1 className="mt-2 text-4xl font-bold">Risk and provider controls</h1>
      </div>
      <ApiErrorBanner error={error} />
      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-2xl border border-borderline bg-panel p-5">
          <h2 className="text-xl font-semibold">Watchlist pairs</h2>
          <ul className="mt-3 list-disc pl-5 text-slate-300">
            {instruments.map((instrument) => (
              <li key={instrument}>{instrument}</li>
            ))}
          </ul>
        </section>
        <section className="rounded-2xl border border-borderline bg-panel p-5">
          <h2 className="text-xl font-semibold">Score thresholds</h2>
          <p className="mt-3 text-slate-300">
            Recommend &gt;= 75, strong &gt;= 85, watchlist 65-74, reject below 65. Reward/risk must be &gt;= 1.5.
          </p>
        </section>
        <section className="rounded-2xl border border-borderline bg-panel p-5">
          <h2 className="text-xl font-semibold">Feature flags</h2>
          <div className="mt-3 space-y-2">
            {Object.entries(health.feature_flags).map(([flag, enabled]) => (
              <p key={flag} className="text-sm">
                <span className={enabled ? 'text-emerald-300' : 'text-slate-500'}>{enabled ? 'ON' : 'OFF'}</span> {flag}
              </p>
            ))}
          </div>
        </section>
        <section className="rounded-2xl border border-borderline bg-panel p-5">
          <h2 className="text-xl font-semibold">Provider mode</h2>
          <p className="mt-3 text-slate-300">
            Mock data: {health.mock_data_enabled ? 'enabled' : 'disabled'}. Live recommendations: {health.live_recommendations_enabled ? 'enabled' : 'disabled'}.
          </p>
        </section>
      </div>
    </div>
  );
}
