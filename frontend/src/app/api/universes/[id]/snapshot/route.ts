import { NextResponse } from "next/server";

const baseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    const response = await fetch(`${baseUrl}/api/universes/${id}/snapshot`, {
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
      { error: error instanceof Error ? error.message : "failed to snapshot universe" },
      { status: 502 },
    );
  }
}
