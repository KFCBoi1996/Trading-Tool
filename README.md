# Trading Tool

SignalGlass is a market intelligence dashboard with an Apple-inspired visual language,
an embedded market browser, URL-to-ticker detection, live quote/chart data, and
decision-support FX signal workflows.

## Run locally

Install frontend dependencies and start the Next app:

```bash
cd frontend
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

For the backend API, use the backend instructions and environment files in `backend/`.

## Features

- Glass-style responsive dashboard in the real Next frontend at `/dashboard`.
- Built-in market browser toolbar for visiting market pages or direct ticker symbols.
- Copy/open controls for the current ticker URL.
- Ticker resolution from common market URLs such as Yahoo Finance and TradingView.
- Next API quote proxy that returns intraday price data for the full tool UI.
- Deterministic FX recommendation cards, pair details, journal, and admin health pages.
