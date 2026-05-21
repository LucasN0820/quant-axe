import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

const baseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const data = await fetchMarketData("/api/universes");
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch universes" },
      { status: 502 },
    );
  }
}

export async function POST(request: Request) {
  try {
    const response = await fetch(`${baseUrl}/api/universes`, {
      method: "POST",
      cache: "no-store",
      headers: { "content-type": "application/json" },
      body: await request.text(),
      signal: AbortSignal.timeout(12_000),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to create universe" },
      { status: 502 },
    );
  }
}
