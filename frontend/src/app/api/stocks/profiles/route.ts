import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q") ?? "";
  const limit = searchParams.get("limit") ?? "20";

  try {
    const query = new URLSearchParams({ q, limit });
    const data = await fetchMarketData(`/api/stocks/profiles?${query.toString()}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch stock profiles", data: [] },
      { status: 502 },
    );
  }
}
