import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type") ?? "daily";
  try {
    const data = await fetchMarketData(`/api/stock/kline/${symbol}?type=${type}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch kline" },
      { status: 502 },
    );
  }
}
