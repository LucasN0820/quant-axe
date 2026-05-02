import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET() {
  try {
    const data = await fetchMarketData("/api/market/indexes");
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch market indexes" },
      { status: 502 },
    );
  }
}
