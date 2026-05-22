'use client';

import { useEffect, useRef } from 'react';
import type { Candle, Recommendation } from '../types/api';

export function ChartPanel({ candles, recommendation }: { candles: Candle[]; recommendation: Recommendation }) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    let cleanup: (() => void) | undefined;
    async function draw() {
      if (!ref.current || candles.length === 0) return;
      const lw = await import('lightweight-charts');
      const chart = lw.createChart(ref.current, { height: 420, layout: { background: { color: '#101827' }, textColor: '#dbeafe' }, grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } } });
      const anyChart = chart as unknown as { addCandlestickSeries?: (options?: unknown) => { setData: (data: unknown[]) => void }; addSeries?: (series: unknown, options?: unknown) => { setData: (data: unknown[]) => void }; remove: () => void; timeScale: () => { fitContent: () => void } };
      const series = anyChart.addCandlestickSeries ? anyChart.addCandlestickSeries({ upColor: '#22c55e', downColor: '#ef4444', borderVisible: false, wickUpColor: '#22c55e', wickDownColor: '#ef4444' }) : anyChart.addSeries?.((lw as unknown as { CandlestickSeries: unknown }).CandlestickSeries, {});
      series?.setData(candles.map((c) => ({ time: Math.floor(new Date(c.timestamp).getTime() / 1000), open: c.open, high: c.high, low: c.low, close: c.close })));
      anyChart.timeScale().fitContent();
      cleanup = () => anyChart.remove();
    }
    void draw();
    return () => cleanup?.();
  }, [candles]);
  const plan = recommendation.risk_plan;
  const validPlan = plan.entry_low !== null && plan.entry_high !== null && plan.stop_loss !== null && plan.tp1 !== null;
  return (
    <section className="rounded-2xl border border-borderline bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Candles and risk plan</h2>
        <span className="rounded-full border border-borderline px-3 py-1 text-xs">{recommendation.data_status}</span>
      </div>
      <div ref={ref} className="overflow-hidden rounded-xl" />
      {validPlan ? (
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
          <Line label="Entry" value={`${plan.entry_low} - ${plan.entry_high}`} />
          <Line label="Stop" value={String(plan.stop_loss)} />
          <Line label="TP1" value={String(plan.tp1)} />
          <Line label="TP2" value={String(plan.tp2 ?? 'n/a')} />
        </div>
      ) : <p className="mt-4 text-sm text-amber-200">Entry/SL/TP lines are hidden because the risk engine did not produce a complete valid plan.</p>}
    </section>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl bg-black/30 p-3"><p className="text-xs uppercase text-slate-500">{label}</p><p>{value}</p></div>;
}
