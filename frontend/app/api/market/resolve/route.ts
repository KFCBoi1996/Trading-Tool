import { NextResponse } from 'next/server';
import { parseTickerFromUrl } from '../../../../lib/market';

export function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const sourceUrl = searchParams.get('url') ?? '';
  const symbol = parseTickerFromUrl(sourceUrl);

  return NextResponse.json(
    {
      symbol,
      sourceUrl,
      message: symbol ? 'Ticker resolved' : 'Could not infer a ticker from that URL'
    },
    { status: symbol ? 200 : 422 }
  );
}
