'use client';

import { useState, useTransition } from 'react';
import { runScan } from '../lib/api';

export function ScanButton({ instrument }: { instrument?: string }) {
  const [pending, startTransition] = useTransition();
  const [status, setStatus] = useState<string | null>(null);

  function handleClick() {
    setStatus(null);
    startTransition(async () => {
      const { error } = await runScan(instrument);
      if (error) {
        setStatus(`Scan failed: ${error.message}`);
        return;
      }
      setStatus('Scan complete. Reloading…');
      window.location.reload();
    });
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={handleClick}
        disabled={pending}
        className="rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-60"
      >
        {pending ? 'Running scan…' : instrument ? `Scan ${instrument}` : 'Run full scan'}
      </button>
      {status && <span className="text-xs text-slate-300">{status}</span>}
    </div>
  );
}
