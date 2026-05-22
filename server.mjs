import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const publicDir = join(__dirname, "public");
const port = Number(process.env.PORT ?? 3000);

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

const knownPathStopWords = new Set([
  "quote",
  "symbol",
  "symbols",
  "stocks",
  "stock",
  "market",
  "markets",
  "equities",
  "finance",
  "chart",
  "news",
  "investing",
  "watchlist",
]);

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(JSON.stringify(payload));
}

function normalizeTicker(rawValue) {
  if (!rawValue) {
    return "";
  }

  const compact = String(rawValue)
    .trim()
    .replace(/^[$#]/, "")
    .replace(/^(nasdaq|nyse|amex|otc|tsx|lse|asx|hkex|crypto|forex|fx)[:/_-]/i, "")
    .replace(/-(stock|quote|chart|technical-analysis|historical-data)$/i, "")
    .replace(/\.html?$/i, "")
    .toUpperCase();

  const cleaned = compact.replace(/[^A-Z0-9.=^/-]/g, "");
  if (!cleaned || knownPathStopWords.has(cleaned.toLowerCase())) {
    return "";
  }

  return cleaned.slice(0, 24);
}

function parseTickerFromUrl(rawUrl) {
  if (!rawUrl) {
    return "";
  }

  const value = rawUrl.trim();
  if (/^[A-Za-z0-9.=^/-]{1,24}$/.test(value) && !value.includes("/")) {
    return normalizeTicker(value);
  }

  let parsed;
  try {
    parsed = new URL(value.includes("://") ? value : `https://${value}`);
  } catch {
    return normalizeTicker(value);
  }

  const queryKeys = ["symbol", "symbols", "s", "ticker", "tvwidgetsymbol"];
  for (const key of queryKeys) {
    const candidate = parsed.searchParams.get(key);
    const ticker = normalizeTicker(candidate);
    if (ticker) {
      return ticker;
    }
  }

  const pathSegments = parsed.pathname
    .split("/")
    .map((segment) => decodeURIComponent(segment))
    .filter(Boolean);

  for (const segment of pathSegments) {
    const tradingViewMatch = segment.match(/(?:NASDAQ|NYSE|AMEX|OTC|TSX|LSE|ASX|HKEX|FOREXCOM|FX_IDC|CRYPTOCAP)[:_-]([A-Z0-9.=^-]+)/i);
    if (tradingViewMatch) {
      return normalizeTicker(tradingViewMatch[1]);
    }
  }

  for (let index = pathSegments.length - 1; index >= 0; index -= 1) {
    const ticker = normalizeTicker(pathSegments[index]);
    if (ticker && /^[A-Z0-9.=^-]{1,12}$/.test(ticker)) {
      return ticker;
    }
  }

  return "";
}

async function fetchYahooChart(symbol) {
  const encoded = encodeURIComponent(symbol);
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encoded}?interval=1m&range=1d&includePrePost=false`;
  const response = await fetch(url, {
    headers: {
      "accept": "application/json",
      "user-agent": "TradingTool/0.1 (+https://localhost)",
    },
  });

  if (!response.ok) {
    throw new Error(`Market provider returned ${response.status}`);
  }

  const payload = await response.json();
  const result = payload?.chart?.result?.[0];
  if (!result) {
    throw new Error(payload?.chart?.error?.description ?? "No market data returned");
  }

  const meta = result.meta ?? {};
  const quote = result.indicators?.quote?.[0] ?? {};
  const timestamps = result.timestamp ?? [];
  const close = quote.close ?? [];
  const points = timestamps
    .map((timestamp, index) => ({
      time: new Date(timestamp * 1000).toISOString(),
      price: close[index],
    }))
    .filter((point) => Number.isFinite(point.price));

  const price = Number(meta.regularMarketPrice ?? points.at(-1)?.price ?? 0);
  const previousClose = Number(meta.chartPreviousClose ?? meta.previousClose ?? 0);
  const change = previousClose ? price - previousClose : 0;
  const changePercent = previousClose ? (change / previousClose) * 100 : 0;

  return {
    symbol: meta.symbol ?? symbol,
    name: meta.longName ?? meta.shortName ?? meta.instrumentType ?? symbol,
    exchange: meta.fullExchangeName ?? meta.exchangeName ?? "Market",
    currency: meta.currency ?? "USD",
    price,
    previousClose,
    change,
    changePercent,
    marketState: meta.marketState ?? "UNKNOWN",
    regularMarketTime: meta.regularMarketTime
      ? new Date(meta.regularMarketTime * 1000).toISOString()
      : new Date().toISOString(),
    points: points.slice(-120),
  };
}

async function handleApi(request, response, url) {
  if (url.pathname === "/api/resolve") {
    const sourceUrl = url.searchParams.get("url") ?? "";
    const symbol = parseTickerFromUrl(sourceUrl);
    sendJson(response, symbol ? 200 : 422, {
      symbol,
      sourceUrl,
      message: symbol ? "Ticker resolved" : "Could not infer a ticker from that URL",
    });
    return;
  }

  if (url.pathname === "/api/quote") {
    const symbol = normalizeTicker(url.searchParams.get("symbol"));
    if (!symbol) {
      sendJson(response, 400, { error: "A ticker symbol is required" });
      return;
    }

    try {
      const quote = await fetchYahooChart(symbol);
      sendJson(response, 200, quote);
    } catch (error) {
      sendJson(response, 502, {
        error: error instanceof Error ? error.message : "Unable to fetch market data",
      });
    }
    return;
  }

  sendJson(response, 404, { error: "Unknown API route" });
}

async function serveStatic(request, response, url) {
  const requestedPath = url.pathname === "/" ? "/index.html" : url.pathname;
  const safePath = normalize(decodeURIComponent(requestedPath)).replace(/^(\.\.[/\\])+/, "");
  const filePath = join(publicDir, safePath);

  if (!filePath.startsWith(publicDir)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  try {
    const file = await readFile(filePath);
    response.writeHead(200, {
      "content-type": mimeTypes[extname(filePath)] ?? "application/octet-stream",
    });
    response.end(file);
  } catch {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}

const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);

  if (url.pathname.startsWith("/api/")) {
    await handleApi(request, response, url);
    return;
  }

  await serveStatic(request, response, url);
});

server.listen(port, () => {
  console.log(`Trading Tool running at http://localhost:${port}`);
});
