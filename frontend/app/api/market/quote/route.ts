import { NextResponse } from 'next/server';
import { fetchYahooChart, normalizeTicker } from '../../../../lib/market';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = normalizeTicker(searchParams.get('symbol'));

  if (!symbol) {
    return NextResponse.json({ error: 'A ticker symbol is required' }, { status: 400 });
  }

  try {
    const quote = await fetchYahooChart(symbol);
    return NextResponse.json(quote);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unable to fetch market data' },
      { status: 502 }
    );
  }
}
