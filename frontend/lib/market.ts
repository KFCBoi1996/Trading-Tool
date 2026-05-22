const knownPathStopWords = new Set([
  'quote',
  'symbol',
  'symbols',
  'stocks',
  'stock',
  'market',
  'markets',
  'equities',
  'finance',
  'chart',
  'news',
  'investing',
  'watchlist'
]);

export interface MarketPoint {
  time: string;
  price: number;
}

export interface MarketQuote {
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  price: number;
  previousClose: number;
  change: number;
  changePercent: number;
  marketState: string;
  regularMarketTime: string;
  points: MarketPoint[];
}

export function normalizeTicker(rawValue: string | null | undefined) {
  if (!rawValue) return '';

  const compact = String(rawValue)
    .trim()
    .replace(/^[$#]/, '')
    .replace(/^(nasdaq|nyse|amex|otc|tsx|lse|asx|hkex|crypto|forex|fx)[:/_-]/i, '')
    .replace(/-(stock|quote|chart|technical-analysis|historical-data)$/i, '')
    .replace(/\.html?$/i, '')
    .toUpperCase();

  const cleaned = compact.replace(/[^A-Z0-9.=^/-]/g, '');
  if (!cleaned || knownPathStopWords.has(cleaned.toLowerCase())) return '';

  return cleaned.slice(0, 24);
}

export function parseTickerFromUrl(rawUrl: string | null | undefined) {
  if (!rawUrl) return '';

  const value = rawUrl.trim();
  if (/^[A-Za-z0-9.=^/-]{1,24}$/.test(value) && !value.includes('/')) {
    return normalizeTicker(value);
  }

  let parsed: URL;
  try {
    parsed = new URL(value.includes('://') ? value : `https://${value}`);
  } catch {
    return normalizeTicker(value);
  }

  for (const key of ['symbol', 'symbols', 's', 'ticker', 'tvwidgetsymbol']) {
    const ticker = normalizeTicker(parsed.searchParams.get(key));
    if (ticker) return ticker;
  }

  const pathSegments = parsed.pathname
    .split('/')
    .map((segment) => decodeURIComponent(segment))
    .filter(Boolean);

  for (const segment of pathSegments) {
    const tradingViewMatch = segment.match(/(?:NASDAQ|NYSE|AMEX|OTC|TSX|LSE|ASX|HKEX|FOREXCOM|FX_IDC|CRYPTOCAP)[:_-]([A-Z0-9.=^-]+)/i);
    if (tradingViewMatch) return normalizeTicker(tradingViewMatch[1]);
  }

  for (let index = pathSegments.length - 1; index >= 0; index -= 1) {
    const ticker = normalizeTicker(pathSegments[index]);
    if (ticker && /^[A-Z0-9.=^-]{1,12}$/.test(ticker)) return ticker;
  }

  return '';
}

export async function fetchYahooChart(symbol: string): Promise<MarketQuote> {
  const encoded = encodeURIComponent(symbol);
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encoded}?interval=1m&range=1d&includePrePost=false`;
  const response = await fetch(url, {
    headers: {
      accept: 'application/json',
      'user-agent': 'SignalGlass/0.1'
    },
    cache: 'no-store'
  });

  if (!response.ok) {
    throw new Error(`Market provider returned ${response.status}`);
  }

  const payload = await response.json();
  const result = payload?.chart?.result?.[0];
  if (!result) {
    throw new Error(payload?.chart?.error?.description ?? 'No market data returned');
  }

  const meta = result.meta ?? {};
  const quote = result.indicators?.quote?.[0] ?? {};
  const timestamps: number[] = result.timestamp ?? [];
  const close: Array<number | null> = quote.close ?? [];
  const points = timestamps
    .map((timestamp, index) => ({
      time: new Date(timestamp * 1000).toISOString(),
      price: close[index]
    }))
    .filter((point): point is MarketPoint => Number.isFinite(point.price));

  const price = Number(meta.regularMarketPrice ?? points.at(-1)?.price ?? 0);
  const previousClose = Number(meta.chartPreviousClose ?? meta.previousClose ?? 0);
  const change = previousClose ? price - previousClose : 0;
  const changePercent = previousClose ? (change / previousClose) * 100 : 0;

  return {
    symbol: meta.symbol ?? symbol,
    name: meta.longName ?? meta.shortName ?? meta.instrumentType ?? symbol,
    exchange: meta.fullExchangeName ?? meta.exchangeName ?? 'Market',
    currency: meta.currency ?? 'USD',
    price,
    previousClose,
    change,
    changePercent,
    marketState: meta.marketState ?? 'UNKNOWN',
    regularMarketTime: meta.regularMarketTime
      ? new Date(meta.regularMarketTime * 1000).toISOString()
      : new Date().toISOString(),
    points: points.slice(-120)
  };
}
