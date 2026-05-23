import type { Candle, Health, Recommendation } from '../types/api';

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  code?: string;
  requestId?: string;

  constructor(message: string, status: number, code?: string, requestId?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

interface ApiResult<T> {
  data: T;
  error: ApiError | null;
}

async function apiFetch<T>(path: string, fallback: T, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...init, cache: 'no-store' });
    if (!response.ok) {
      let code: string | undefined;
      let requestId: string | undefined;
      let message = `Request failed with status ${response.status}`;
      try {
        const body = await response.json();
        code = body?.error?.code;
        requestId = body?.error?.request_id;
        message = body?.error?.message || message;
      } catch {
        /* ignore json parse errors */
      }
      return { data: fallback, error: new ApiError(message, response.status, code, requestId) };
    }
    return { data: (await response.json()) as T, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error';
    return { data: fallback, error: new ApiError(message, 0, 'network_error') };
  }
}

export const instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD'];

export const instrumentPrecision: Record<string, number> = {
  EUR_USD: 5,
  GBP_USD: 5,
  AUD_USD: 5,
  USD_CAD: 5,
  USD_JPY: 3
};

export function formatPrice(value: number | null | undefined, instrument: string): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
  return value.toFixed(instrumentPrecision[instrument] ?? 5);
}

export function emptyRecommendation(instrument = 'EUR_USD'): Recommendation {
  return {
    signal_id: 'unavailable',
    instrument,
    data_status: 'UNAVAILABLE',
    data_provider: 'UNAVAILABLE',
    latest_candle_timestamp: null,
    latest_quote_timestamp: null,
    data_quality_passed: false,
    data_quality_rejection_reason: 'Backend unavailable or no scan has completed.',
    strategy_signal: {
      strategy_id: 'unavailable',
      strategy_version: '0.0.0',
      strategy_family: 'none',
      direction: 'none',
      status: 'rejected',
      entry_zone: { low: null, high: null },
      suggested_stop: null,
      suggested_targets: [null, null],
      evidence: [],
      risk_flags: [],
      raw_confidence: 0,
      data_status: 'UNAVAILABLE',
      is_mock: false
    },
    regime: {
      trend_state: 'neutral',
      trend_strength: 0,
      range_strength: 0,
      volatility_state: 'normal',
      session_state: 'low_liquidity',
      preferred_strategies: [],
      blocked_strategies: []
    },
    news_risk: { news_risk_status: 'unavailable', blackout_active: false, next_event: null },
    ranking: { final_score: 0, decision: 'no_trade', rejection_reason: 'Backend unavailable.', score_breakdown: {} },
    risk_plan: {
      entry_type: 'none',
      entry_low: null,
      entry_high: null,
      stop_loss: null,
      tp1: null,
      tp2: null,
      rr_to_tp1: null,
      rr_to_tp2: null,
      invalidation: 'Unavailable',
      missed_entry: false,
      rejection_reason: 'Backend unavailable.'
    },
    ai_analysis: {
      trade_thesis: 'Unavailable. No AI or rules summary was generated.',
      why_take: [],
      why_not_take: [{ text: 'Required backend data is unavailable.', evidence_ids: [] }],
      final_note: 'Decision-support only. No trade execution.'
    },
    risk_review: {
      risk_review_passed: false,
      rejection_reason: 'Backend unavailable.',
      warnings: [],
      recommended_display_mode: 'no_trade'
    },
    final_arbiter: {
      final_decision: 'REJECTED_DATA_QUALITY',
      display_mode: 'no_trade',
      allowed_to_alert: false,
      rejection_reason: 'Backend unavailable.'
    },
    no_trade_explanation: {
      reasons: ['Backend unavailable.'],
      could_become_valid_if: ['Start the backend service and configure data providers.'],
      expired: false,
      blocked_by_mock_data: false
    },
    is_mock: false
  };
}

export async function getRecommendation(instrument: string): Promise<ApiResult<Recommendation>> {
  return apiFetch<Recommendation>(`/api/recommendations/${instrument}`, emptyRecommendation(instrument));
}

export async function getCandles(instrument: string, timeframe = 'M15'): Promise<ApiResult<Candle[]>> {
  return apiFetch<Candle[]>(`/api/candles/${instrument}?timeframe=${timeframe}&limit=120`, []);
}

export async function getHealth(): Promise<ApiResult<Health>> {
  return apiFetch<Health>('/api/health', {
    status: 'degraded',
    service: 'frontend-fallback',
    mock_data_enabled: false,
    live_recommendations_enabled: false,
    feature_flags: {},
    checks: { backend: 'unavailable' }
  });
}

export async function getJournal(): Promise<ApiResult<Array<Record<string, unknown>>>> {
  return apiFetch<Array<Record<string, unknown>>>('/api/journal', []);
}

export async function getAdminHealth(): Promise<ApiResult<Record<string, unknown>>> {
  return apiFetch<Record<string, unknown>>('/api/admin/health', {
    status: 'degraded',
    reason: 'Backend unavailable'
  });
}

export async function getRecommendationBySignal(signalId: string): Promise<ApiResult<Record<string, unknown>>> {
  return apiFetch<Record<string, unknown>>(`/api/recommendations/signal/${signalId}`, {});
}

export async function runScan(instrument?: string): Promise<ApiResult<Recommendation | Recommendation[]>> {
  const path = instrument ? `/api/scan/${instrument}` : '/api/scan';
  return apiFetch<Recommendation | Recommendation[]>(path, instrument ? emptyRecommendation(instrument) : [], { method: 'POST' });
}
