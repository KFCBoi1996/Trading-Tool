import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'FX Signal Intelligence MVP',
  description: 'Decision-support forex signal intelligence. No trade execution.'
};

const nav = [
  ['Dashboard', '/dashboard'], ['Strategy Lab', '/strategy-lab'], ['Journal', '/journal'], ['Settings', '/settings'], ['Admin Health', '/admin/health']
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-borderline bg-panel/80 px-6 py-4">
            <div className="mx-auto flex max-w-7xl flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <Link href="/dashboard" className="text-xl font-semibold">FX Signal Intelligence</Link>
              <nav className="flex flex-wrap gap-3 text-sm text-slate-300">
                {nav.map(([label, href]) => <Link key={href} href={href} className="rounded-full border border-borderline px-3 py-1 hover:border-sky-400">{label}</Link>)}
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
          <footer className="border-t border-borderline px-6 py-4 text-center text-xs text-slate-400">
            This app is a decision-support and research tool only. It does not execute trades. Forex trading involves substantial risk. No output is guaranteed.
          </footer>
        </div>
      </body>
    </html>
  );
}
