import { instruments } from '../../lib/api';

const strategies = ['ema_trend_pullback', 'breakout_retest', 'asian_range_breakout', 'london_continuation', 'rsi_divergence_reversal', 'macd_momentum_continuation', 'bollinger_mean_reversion', 'donchian_breakout', 'adx_trend_strength_filter', 'engulfing_at_structure', 'liquidity_sweep_reversal', 'multi_timeframe_alignment'];

export default function StrategyLabPage() {
  return (
    <div className="space-y-6">
      <div><p className="text-sm uppercase tracking-wide text-sky-300">Strategy Lab</p><h1 className="mt-2 text-4xl font-bold">Champion/challenger scaffold</h1></div>
      <section className="rounded-2xl border border-borderline bg-panel p-5">
        <p className="text-slate-300">Backtest metrics are displayed only after calculated from stored candles. The MVP returns “Backtest unavailable” until a real historical sample exists.</p>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {strategies.map((strategy) => <div key={strategy} className="rounded-xl bg-black/25 p-4"><h2 className="font-semibold">{strategy}</h2><p className="text-sm text-slate-400">Version 1.0.0 | Champion candidate | Pairs: {instruments.join(', ')}</p><p className="mt-2 text-sm text-amber-200">Backtest unavailable; no performance claims.</p></div>)}
        </div>
      </section>
    </div>
  );
}
