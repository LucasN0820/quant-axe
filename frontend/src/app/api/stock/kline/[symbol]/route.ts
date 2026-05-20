import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type") ?? "daily";
  const adjust = searchParams.get("adjust") ?? "none";
  try {
    const query = new URLSearchParams({ type, adjust });
    const data = await fetchMarketData(`/api/stock/kline/${symbol}?${query.toString()}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch kline" },
      { status: 502 },
    );
  }
}
