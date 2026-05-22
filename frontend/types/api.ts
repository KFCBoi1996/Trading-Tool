export type DataStatus = 'LIVE' | 'DELAYED' | 'MOCK' | 'STALE' | 'DEGRADED' | 'UNAVAILABLE';

export interface Candle {
  provider: string;
  instrument: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
  complete: boolean;
  data_status: DataStatus;
  is_mock: boolean;
}

export interface Recommendation {
  signal_id: string;
  instrument: string;
  data_status: DataStatus;
  data_provider: string;
  latest_candle_timestamp: string | null;
  latest_quote_timestamp: string | null;
  data_quality_passed: boolean;
  data_quality_rejection_reason: string | null;
  strategy_signal: {
    strategy_id: string;
    strategy_version: string;
    strategy_family: string;
    direction: 'long' | 'short' | 'none';
    status: 'active' | 'watchlist' | 'rejected';
    entry_zone: { low: number | null; high: number | null };
    suggested_stop: number | null;
    suggested_targets: Array<number | null>;
    evidence: Array<{ evidence_id: string; text: string; source: string }>;
    risk_flags: Array<{ flag_id: string; text: string }>;
    raw_confidence: number;
    data_status: DataStatus;
    is_mock: boolean;
  };
  regime: {
    trend_state: string;
    trend_strength: number;
    range_strength: number;
    volatility_state: string;
    session_state: string;
    preferred_strategies: string[];
    blocked_strategies: string[];
  };
  news_risk: { news_risk_status: string; blackout_active: boolean; next_event: Record<string, unknown> | null };
  ranking: { final_score: number; decision: string; rejection_reason: string | null; score_breakdown: Record<string, number> };
  risk_plan: {
    entry_type: string;
    entry_low: number | null;
    entry_high: number | null;
    stop_loss: number | null;
    tp1: number | null;
    tp2: number | null;
    rr_to_tp1: number | null;
    rr_to_tp2: number | null;
    invalidation: string;
    missed_entry: boolean;
    rejection_reason: string | null;
  };
  ai_analysis: { trade_thesis: string; why_take: Array<{ text: string; evidence_ids: string[] }>; why_not_take: Array<{ text: string; evidence_ids: string[] }>; final_note: string };
  risk_review: { risk_review_passed: boolean; rejection_reason: string | null; warnings: string[]; recommended_display_mode: string };
  final_arbiter: { final_decision: string; display_mode: 'trade_recommendation' | 'watchlist' | 'no_trade'; allowed_to_alert: boolean; rejection_reason: string | null };
  no_trade_explanation: { reasons: string[]; could_become_valid_if: string[]; expired: boolean; blocked_by_mock_data: boolean };
  audit_id?: string | null;
  is_mock: boolean;
}

export interface Health {
  status: 'healthy' | 'degraded';
  service: string;
  mock_data_enabled: boolean;
  live_recommendations_enabled: boolean;
  feature_flags: Record<string, boolean>;
  checks: Record<string, string>;
}
