import Link from 'next/link';
import { ApiErrorBanner } from '../../components/ApiErrorBanner';
import { getJournal } from '../../lib/api';

export default async function JournalPage() {
  const { data: rows, error } = await getJournal();
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-sky-300">Signal Journal</p>
        <h1 className="mt-2 text-4xl font-bold">Every decision is journaled</h1>
      </div>
      <ApiErrorBanner error={error} />
      <section className="overflow-hidden rounded-2xl border border-borderline bg-panel">
        <table className="w-full text-left text-sm">
          <thead className="bg-black/30 text-slate-400">
            <tr>
              <th className="p-3">Created</th>
              <th>Instrument</th>
              <th>Decision</th>
              <th>Reason</th>
              <th>Data</th>
              <th>Signal</th>
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((row) => (
                <tr key={String(row.id)} className="border-t border-borderline">
                  <td className="p-3">{String(row.created_at)}</td>
                  <td>{String(row.instrument)}</td>
                  <td>{String(row.final_decision)}</td>
                  <td>{String(row.rejection_reason || '')}</td>
                  <td>{String(row.data_status)}</td>
                  <td>
                    {row.signal_id ? (
                      <Link className="text-sky-300" href={`/signals/${String(row.signal_id)}`}>
                        open
                      </Link>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="p-6 text-slate-400" colSpan={6}>
                  No journal rows yet. Run a scan from the dashboard or POST /api/scan.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
