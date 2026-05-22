import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(request: Request) {
  const { search } = new URL(request.url);
  try {
    const data = await fetchMarketData(`/api/market/snapshot${search}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch market snapshot" },
      { status: 502 },
    );
  }
}
