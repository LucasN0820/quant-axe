import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q") ?? "";

  try {
    const data = await fetchMarketData(`/api/stocks/search?q=${encodeURIComponent(q)}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to search stocks", data: [] },
      { status: 502 },
    );
  }
}

