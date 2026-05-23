'use client';

import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import type { MarketQuote } from '../lib/market';

const defaultUrl = 'https://finance.yahoo.com/quote/AAPL';
const sampleTickers = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'BTC-USD'];

function frameUrlFor(value: string) {
  const input = value.trim();
  if (!input) return defaultUrl;
  if (/^[A-Za-z0-9.=^-]{1,24}$/.test(input)) {
    return `https://finance.yahoo.com/quote/${encodeURIComponent(input.toUpperCase())}`;
  }
  return input.includes('://') ? input : `https://${input}`;
}

function formatCurrency(value: number, currency = 'USD') {
  if (!Number.isFinite(value)) return '--';
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    maximumFractionDigits: value > 1000 ? 0 : 2
  }).format(value);
}

function chartPath(points: MarketQuote['points']) {
  const prices = points.map((point) => point.price).filter(Number.isFinite);
  if (prices.length < 2) return '';

  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const width = 720;
  const height = 220;
  const padding = 12;

  return prices
    .map((price, index) => {
      const x = padding + (index / (prices.length - 1)) * (width - padding * 2);
      const y = height - padding - ((price - min) / range) * (height - padding * 2);
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(' ');
}

export function MarketBrowser() {
  const [address, setAddress] = useState(defaultUrl);
  const [frameSrc, setFrameSrc] = useState('');
  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [status, setStatus] = useState('AAPL is loaded as the default live instrument.');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const path = useMemo(() => chartPath(quote?.points ?? []), [quote]);
  const positive = (quote?.change ?? 0) >= 0;

  useEffect(() => {
    void loadQuote('AAPL');
  }, []);

  async function loadQuote(symbol: string) {
    setLoading(true);
    setStatus(`Loading ${symbol.toUpperCase()}...`);
    try {
      const response = await fetch(`/api/market/quote?symbol=${encodeURIComponent(symbol)}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? 'Quote request failed');
      setQuote(payload as MarketQuote);
      setStatus(`${payload.symbol} live quote updated.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Unable to load market data.');
    } finally {
      setLoading(false);
    }
  }

  async function pullLiveData(source = address) {
    setLoading(true);
    setStatus('Resolving ticker from URL...');
    try {
      const response = await fetch(`/api/market/resolve?url=${encodeURIComponent(source)}`);
      const payload = await response.json();
      if (!response.ok || !payload.symbol) throw new Error(payload.message ?? 'Could not infer ticker');
      await loadQuote(payload.symbol);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Unable to pull ticker data.');
      setLoading(false);
    }
  }

  function submitBrowser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextUrl = frameUrlFor(address);
    setAddress(nextUrl);
    setFrameSrc(nextUrl);
  }

  async function copyUrl() {
    const nextUrl = frameUrlFor(address || frameSrc);
    setAddress(nextUrl);
    try {
      await navigator.clipboard.writeText(nextUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setStatus('Clipboard access was blocked. Select the address field to copy manually.');
    }
  }

  return (
    <section className="overflow-hidden rounded-[2rem] border border-white/15 bg-white/[0.08] shadow-2xl shadow-sky-950/30 backdrop-blur">
      <div className="grid gap-0 xl:grid-cols-[minmax(0,1fr)_440px]">
        <div className="relative min-h-[560px] bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.25),transparent_32rem),linear-gradient(135deg,#060914,#111827)] p-6 md:p-8">
          <div className="absolute right-8 top-8 h-36 w-36 rounded-full bg-sky-400/20 blur-3xl" />
          <div className="relative flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-rose-400" />
            <span className="h-3 w-3 rounded-full bg-amber-300" />
            <span className="h-3 w-3 rounded-full bg-emerald-400" />
          </div>

          <div className="relative mt-12 max-w-4xl">
            <p className="text-xs font-bold uppercase tracking-[0.35em] text-sky-200">SignalGlass browser</p>
            <h2 className="mt-4 text-5xl font-black leading-[0.9] tracking-[-0.08em] text-white md:text-7xl">
              Paste a market URL. Watch the ticker become live intelligence.
            </h2>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
              This dashboard now owns the Apple-like experience directly in the Next app, so the
              visual redesign appears on the actual deployed surface instead of a separate static page.
            </p>
          </div>

          <div className="relative mt-10 rounded-[1.75rem] border border-white/15 bg-white/10 p-4 shadow-2xl backdrop-blur">
            <form onSubmit={submitBrowser} className="flex flex-col gap-3 lg:flex-row">
              <label className="sr-only" htmlFor="market-url">Market URL or ticker</label>
              <input
                id="market-url"
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                className="min-w-0 flex-1 rounded-full border border-white/15 bg-white px-5 py-3 text-slate-950 outline-none"
                placeholder="Paste a ticker URL, e.g. https://finance.yahoo.com/quote/NVDA"
              />
              <button className="rounded-full bg-white px-5 py-3 font-bold text-slate-950" type="submit">Go</button>
              <button className="rounded-full bg-sky-500 px-5 py-3 font-bold text-white" onClick={() => void pullLiveData()} type="button">
                {loading ? 'Loading...' : 'Pull live data'}
              </button>
            </form>
            <div className="mt-3 flex flex-wrap gap-2">
              <button className="rounded-full border border-white/15 px-4 py-2 text-sm text-white" onClick={() => void copyUrl()} type="button">
                {copied ? 'Copied' : 'Copy URL'}
              </button>
              <button className="rounded-full border border-white/15 px-4 py-2 text-sm text-white" onClick={() => window.open(frameUrlFor(address), '_blank', 'noopener,noreferrer')} type="button">
                Open URL
              </button>
              {sampleTickers.map((symbol) => (
                <button
                  key={symbol}
                  className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-sky-100 hover:bg-white/20"
                  onClick={() => {
                    const nextUrl = `https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}`;
                    setAddress(nextUrl);
                    void loadQuote(symbol);
                  }}
                  type="button"
                >
                  {symbol}
                </button>
              ))}
            </div>
          </div>

          <div className="relative mt-6 overflow-hidden rounded-[1.75rem] border border-white/15 bg-white">
            {frameSrc ? (
              <iframe className="h-[420px] w-full bg-white" src={frameSrc} title="Built-in market browser" referrerPolicy="no-referrer" />
            ) : (
              <div className="grid h-[420px] place-items-center bg-[radial-gradient(circle_at_center,rgba(14,165,233,0.16),transparent_26rem),linear-gradient(180deg,#f8fbff,#e9eef8)] p-8 text-center text-slate-900">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.3em] text-sky-600">On-demand browser</p>
                  <h3 className="mt-3 text-4xl font-black tracking-[-0.06em]">Press Go to load a market page.</h3>
                  <p className="mx-auto mt-3 max-w-xl text-slate-600">
                    The app no longer auto-loads a third-party iframe on startup, so the redesigned GUI remains visible and fast.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <aside className="bg-white p-6 text-slate-950 md:p-8">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sky-600">Live instrument</p>
          <div className="mt-5 flex items-start justify-between gap-4">
            <div>
              <h3 className="text-4xl font-black tracking-[-0.06em]">{quote?.symbol ?? 'AAPL'}</h3>
              <p className="mt-1 text-slate-500">{quote?.name ?? 'Load a symbol to populate live data.'}</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-sm font-bold ${positive ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
              {quote ? `${positive ? '+' : ''}${quote.changePercent.toFixed(2)}%` : '--'}
            </span>
          </div>

          <div className="mt-8">
            <p className="text-6xl font-black tracking-[-0.08em]">
              {quote ? formatCurrency(quote.price, quote.currency) : '$0.00'}
            </p>
            <p className="mt-2 text-sm text-slate-500">{status}</p>
          </div>

          <svg className="mt-8 h-56 w-full" viewBox="0 0 720 220" role="img" aria-label="Intraday price chart">
            <defs>
              <linearGradient id="signalLine" x1="0" x2="1" y1="0" y2="0">
                <stop stopColor={positive ? '#10b981' : '#f43f5e'} />
                <stop offset="1" stopColor="#0ea5e9" />
              </linearGradient>
            </defs>
            {[0, 1, 2, 3].map((line) => (
              <line key={line} x1="12" x2="708" y1={24 + line * 54} y2={24 + line * 54} stroke="#e2e8f0" strokeWidth="1" />
            ))}
            {path ? <path d={path} fill="none" stroke="url(#signalLine)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="6" /> : null}
          </svg>

          <div className="mt-8 grid grid-cols-2 gap-3 text-sm">
            <Metric label="Exchange" value={quote?.exchange ?? '--'} />
            <Metric label="Currency" value={quote?.currency ?? '--'} />
            <Metric label="Previous close" value={quote ? formatCurrency(quote.previousClose, quote.currency) : '--'} />
            <Metric label="Market state" value={quote?.marketState ?? '--'} />
          </div>
        </aside>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-100 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 font-bold text-slate-950">{value}</p>
    </div>
  );
}
