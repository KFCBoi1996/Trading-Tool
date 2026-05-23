'use client';

import { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts';
import { formatPrice, instrumentPrecision } from '../lib/api';
import type { Candle, Recommendation } from '../types/api';

export function ChartPanel({ candles, recommendation }: { candles: Candle[]; recommendation: Recommendation }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;
    const precision = instrumentPrecision[recommendation.instrument] ?? 5;
    const chart = createChart(containerRef.current, {
      height: 420,
      layout: { background: { color: '#101827' }, textColor: '#dbeafe' },
      grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } },
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderColor: '#243044' }
    });
    const chartWithSeries = chart as unknown as {
      addCandlestickSeries: (opts: Record<string, unknown>) => ISeriesApi<'Candlestick'>;
    };
    const series = chartWithSeries.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      priceFormat: { type: 'price', precision, minMove: Math.pow(10, -precision) }
    });
    series.setData(
      candles.map((c) => ({
        time: Math.floor(new Date(c.timestamp).getTime() / 1000) as unknown as never,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close
      }))
    );
    const plan = recommendation.risk_plan;
    const lines: Array<{ price: number; title: string; color: string }> = [];
    if (plan.entry_low !== null) lines.push({ price: plan.entry_low, title: 'Entry low', color: '#38bdf8' });
    if (plan.entry_high !== null) lines.push({ price: plan.entry_high, title: 'Entry high', color: '#38bdf8' });
    if (plan.stop_loss !== null) lines.push({ price: plan.stop_loss, title: 'Stop', color: '#f87171' });
    if (plan.tp1 !== null) lines.push({ price: plan.tp1, title: 'TP1', color: '#34d399' });
    if (plan.tp2 !== null) lines.push({ price: plan.tp2, title: 'TP2', color: '#a7f3d0' });
    const seriesWithLines = series as unknown as {
      createPriceLine: (opts: { price: number; color: string; lineWidth: number; lineStyle: number; title: string }) => void;
    };
    for (const line of lines) {
      seriesWithLines.createPriceLine({ price: line.price, color: line.color, lineWidth: 1, lineStyle: 2, title: line.title });
    }
    chart.timeScale().fitContent();
    chartRef.current = chart;
    return () => chart.remove();
  }, [candles, recommendation]);

  const plan = recommendation.risk_plan;
  const validPlan = plan.entry_low !== null && plan.entry_high !== null && plan.stop_loss !== null && plan.tp1 !== null;
  return (
    <section className="rounded-2xl border border-borderline bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Candles and risk plan</h2>
        <span className="rounded-full border border-borderline px-3 py-1 text-xs">{recommendation.data_status}</span>
      </div>
      <div ref={containerRef} className="overflow-hidden rounded-xl" />
      {validPlan ? (
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
          <Line label="Entry" value={`${formatPrice(plan.entry_low, recommendation.instrument)} - ${formatPrice(plan.entry_high, recommendation.instrument)}`} />
          <Line label="Stop" value={formatPrice(plan.stop_loss, recommendation.instrument)} />
          <Line label="TP1" value={formatPrice(plan.tp1, recommendation.instrument)} />
          <Line label="TP2" value={formatPrice(plan.tp2, recommendation.instrument)} />
        </div>
      ) : (
        <p className="mt-4 text-sm text-amber-200">Entry/SL/TP lines are hidden because the risk engine did not produce a complete valid plan.</p>
      )}
    </section>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-black/30 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p>{value}</p>
    </div>
  );
}
