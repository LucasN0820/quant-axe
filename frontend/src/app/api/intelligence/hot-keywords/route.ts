import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET() {
  try {
    const data = await fetchMarketData("/api/intelligence/hot-keywords");
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch hot keywords", data: [] },
      { status: 502 },
    );
  }
}

