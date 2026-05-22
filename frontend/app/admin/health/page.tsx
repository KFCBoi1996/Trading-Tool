import { getAdminHealth } from '../../../lib/api';

export default async function AdminHealthPage() {
  const health = await getAdminHealth();
  return (
    <div className="space-y-6">
      <div><p className="text-sm uppercase tracking-wide text-sky-300">Admin</p><h1 className="mt-2 text-4xl font-bold">System Health</h1></div>
      <section className="rounded-2xl border border-borderline bg-panel p-5">
        <pre className="overflow-auto rounded-xl bg-black/40 p-4 text-xs text-slate-200">{JSON.stringify(health, null, 2)}</pre>
      </section>
    </div>
  );
}
