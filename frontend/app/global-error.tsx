'use client';

import { useEffect } from 'react';

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#070b12] p-10 text-slate-100">
        <div className="mx-auto max-w-2xl rounded-2xl border border-rose-700 bg-rose-950/40 p-6">
          <h1 className="text-2xl font-semibold text-rose-200">Something went wrong</h1>
          <p className="mt-2 text-rose-100">
            The frontend encountered an unexpected error. Reload the page or try again. No trade orders are or were placed by this app.
          </p>
          <button
            type="button"
            onClick={reset}
            className="mt-4 rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400"
          >
            Try again
          </button>
          {error.digest && <p className="mt-3 text-xs text-rose-300">digest: {error.digest}</p>}
        </div>
      </body>
    </html>
  );
}
