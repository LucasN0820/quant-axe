import { NextResponse } from "next/server";

const baseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type") ?? "";

  try {
    const response = await fetch(
      `${baseUrl}/api/data/jobs/run?type=${encodeURIComponent(type)}`,
      {
        method: "POST",
        cache: "no-store",
        signal: AbortSignal.timeout(12_000),
      },
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to run data job" },
      { status: 502 },
    );
  }
}
