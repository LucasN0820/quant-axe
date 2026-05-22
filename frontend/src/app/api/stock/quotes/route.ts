import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(request: Request) {
  const { search } = new URL(request.url);
  try {
    const data = await fetchMarketData(`/api/stock/quotes${search}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch quotes" },
      { status: 502 },
    );
  }
}
