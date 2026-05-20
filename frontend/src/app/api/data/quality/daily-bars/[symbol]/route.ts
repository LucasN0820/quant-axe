import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;
  const { search } = new URL(request.url);

  try {
    const data = await fetchMarketData(`/api/data/quality/daily-bars/${symbol}${search}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch data quality report" },
      { status: 502 },
    );
  }
}
