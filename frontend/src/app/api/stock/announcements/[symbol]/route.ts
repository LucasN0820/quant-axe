import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;

  try {
    const data = await fetchMarketData(`/api/stock/announcements/${symbol}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch announcements", data: [] },
      { status: 502 },
    );
  }
}

