const state = {
  symbol: "AAPL",
  quote: null,
};

const elements = {
  marketUrl: document.querySelector("#marketUrl"),
  marketFrame: document.querySelector("#marketFrame"),
  browserContent: document.querySelector(".browser-content"),
  browserForm: document.querySelector("#browserForm"),
  captureTicker: document.querySelector("#captureTicker"),
  copyUrl: document.querySelector("#copyUrl"),
  openUrl: document.querySelector("#openUrl"),
  refreshQuote: document.querySelector("#refreshQuote"),
  demoApple: document.querySelector("#demoApple"),
  quoteName: document.querySelector("#quoteName"),
  quoteExchange: document.querySelector("#quoteExchange"),
  tickerPill: document.querySelector("#tickerPill"),
  quotePrice: document.querySelector("#quotePrice"),
  quoteChange: document.querySelector("#quoteChange"),
  previousClose: document.querySelector("#previousClose"),
  currency: document.querySelector("#currency"),
  marketState: document.querySelector("#marketState"),
  lastUpdate: document.querySelector("#lastUpdate"),
  signalTitle: document.querySelector("#signalTitle"),
  signalCopy: document.querySelector("#signalCopy"),
  sampleTickers: document.querySelector("#sampleTickers"),
  priceChart: document.querySelector("#priceChart"),
};

const currencyFormatter = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

function toFrameUrl(value) {
  const input = value.trim();
  if (!input) {
    return "https://finance.yahoo.com/quote/AAPL";
  }

  if (/^[A-Za-z0-9.=^-]{1,24}$/.test(input)) {
    return `https://finance.yahoo.com/quote/${encodeURIComponent(input.toUpperCase())}`;
  }

  return input.includes("://") ? input : `https://${input}`;
}

function formatCurrency(value, currency = "USD") {
  if (!Number.isFinite(value)) {
    return "--";
  }

  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
    maximumFractionDigits: value > 1000 ? 0 : 2,
  }).format(value);
}

function setLoading(symbol) {
  elements.quoteName.textContent = `Loading ${symbol}...`;
  elements.quoteExchange.textContent = "Contacting live market data provider";
  elements.tickerPill.textContent = symbol;
  elements.signalTitle.textContent = "Reading the tape";
  elements.signalCopy.textContent = "Resolving the latest intraday quote and chart points.";
}

function setError(message) {
  elements.quoteName.textContent = "Data unavailable";
  elements.quoteExchange.textContent = message;
  elements.signalTitle.textContent = "Could not complete request";
  elements.signalCopy.textContent =
    "Try a different ticker, paste a direct finance URL, or use a symbol from the quick chips.";
}

function drawChart(points = [], change = 0) {
  const canvas = elements.priceChart;
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 28;

  context.clearRect(0, 0, width, height);
  context.fillStyle = "rgba(255, 255, 255, 0.34)";
  context.fillRect(0, 0, width, height);

  const prices = points.map((point) => point.price).filter(Number.isFinite);
  if (prices.length < 2) {
    context.fillStyle = "#8a93a3";
    context.font = "24px system-ui";
    context.fillText("Chart appears after live data loads", padding, height / 2);
    return;
  }

  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const lineColor = change >= 0 ? "#0a9f64" : "#d83a3a";
  const gradient = context.createLinearGradient(0, padding, 0, height - padding);
  gradient.addColorStop(0, change >= 0 ? "rgba(10, 159, 100, 0.26)" : "rgba(216, 58, 58, 0.24)");
  gradient.addColorStop(1, "rgba(255, 255, 255, 0)");

  const toX = (index) => padding + (index / (prices.length - 1)) * (width - padding * 2);
  const toY = (price) => height - padding - ((price - min) / range) * (height - padding * 2);

  context.strokeStyle = "rgba(17, 19, 24, 0.07)";
  context.lineWidth = 1;
  for (let index = 0; index < 4; index += 1) {
    const y = padding + index * ((height - padding * 2) / 3);
    context.beginPath();
    context.moveTo(padding, y);
    context.lineTo(width - padding, y);
    context.stroke();
  }

  context.beginPath();
  prices.forEach((price, index) => {
    const x = toX(index);
    const y = toY(price);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.lineTo(width - padding, height - padding);
  context.lineTo(padding, height - padding);
  context.closePath();
  context.fillStyle = gradient;
  context.fill();

  context.beginPath();
  prices.forEach((price, index) => {
    const x = toX(index);
    const y = toY(price);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.strokeStyle = lineColor;
  context.lineWidth = 4;
  context.lineJoin = "round";
  context.lineCap = "round";
  context.stroke();
}

function renderQuote(quote) {
  const isPositive = quote.change >= 0;
  const changeClass = isPositive ? "positive" : "negative";
  const signedChange = `${isPositive ? "+" : ""}${quote.change.toFixed(2)}`;
  const signedPercent = `${isPositive ? "+" : ""}${quote.changePercent.toFixed(2)}%`;

  elements.quoteName.textContent = quote.name;
  elements.quoteExchange.textContent = quote.exchange;
  elements.tickerPill.textContent = quote.symbol;
  elements.quotePrice.textContent = formatCurrency(quote.price, quote.currency);
  elements.quoteChange.textContent = `${signedChange} (${signedPercent})`;
  elements.quoteChange.className = `change ${changeClass}`;
  elements.previousClose.textContent = formatCurrency(quote.previousClose, quote.currency);
  elements.currency.textContent = quote.currency;
  elements.marketState.textContent = quote.marketState;
  elements.lastUpdate.textContent = new Date(quote.regularMarketTime).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  elements.signalTitle.textContent = isPositive ? "Momentum is firming" : "Momentum is cooling";
  elements.signalCopy.textContent = `${quote.symbol} is ${signedPercent} against the previous close with ${quote.points.length} intraday observations available.`;
  drawChart(quote.points, quote.change);
}

async function resolveTicker(source) {
  const response = await fetch(`/api/resolve?url=${encodeURIComponent(source)}`);
  const payload = await response.json();
  if (!response.ok || !payload.symbol) {
    throw new Error(payload.message ?? "Could not infer ticker");
  }
  return payload.symbol;
}

async function loadQuote(symbol) {
  state.symbol = symbol.toUpperCase();
  setLoading(state.symbol);

  const response = await fetch(`/api/quote?symbol=${encodeURIComponent(state.symbol)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error ?? "Quote request failed");
  }

  state.quote = payload;
  renderQuote(payload);
}

async function pullLiveData() {
  try {
    const source = elements.marketUrl.value || elements.marketFrame.src;
    const symbol = await resolveTicker(source);
    await loadQuote(symbol);
  } catch (error) {
    setError(error instanceof Error ? error.message : "Unable to pull market data");
  }
}

elements.browserForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const url = toFrameUrl(elements.marketUrl.value);
  elements.marketUrl.value = url;
  elements.marketFrame.src = url;
  elements.browserContent.classList.add("has-loaded");
});

elements.copyUrl.addEventListener("click", async () => {
  const url = toFrameUrl(elements.marketUrl.value || elements.marketFrame.src);
  elements.marketUrl.value = url;
  try {
    await navigator.clipboard.writeText(url);
    elements.copyUrl.textContent = "Copied";
    window.setTimeout(() => {
      elements.copyUrl.textContent = "Copy URL";
    }, 1400);
  } catch {
    elements.marketUrl.select();
  }
});

elements.openUrl.addEventListener("click", () => {
  const url = toFrameUrl(elements.marketUrl.value || elements.marketFrame.src);
  elements.marketUrl.value = url;
  window.open(url, "_blank", "noopener,noreferrer");
});

elements.captureTicker.addEventListener("click", pullLiveData);
elements.refreshQuote.addEventListener("click", () => loadQuote(state.symbol).catch((error) => setError(error.message)));
elements.demoApple.addEventListener("click", () => {
  elements.marketUrl.value = "https://finance.yahoo.com/quote/AAPL";
  loadQuote("AAPL").catch((error) => setError(error.message));
});

elements.sampleTickers.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-symbol]");
  if (!button) {
    return;
  }

  const symbol = button.dataset.symbol;
  elements.marketUrl.value = `https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}`;
  loadQuote(symbol).catch((error) => setError(error.message));
});

elements.marketUrl.value = "https://finance.yahoo.com/quote/AAPL";
drawChart();
loadQuote(state.symbol).catch((error) => {
  elements.quotePrice.textContent = currencyFormatter.format(0);
  setError(error.message);
});
