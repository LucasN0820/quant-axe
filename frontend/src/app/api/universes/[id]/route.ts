import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

const baseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    const data = await fetchMarketData(`/api/universes/${id}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch universe" },
      { status: 502 },
    );
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    const response = await fetch(`${baseUrl}/api/universes/${id}`, {
      method: "PATCH",
      cache: "no-store",
      headers: { "content-type": "application/json" },
      body: await request.text(),
      signal: AbortSignal.timeout(12_000),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to update universe" },
      { status: 502 },
    );
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    const response = await fetch(`${baseUrl}/api/universes/${id}`, {
      method: "DELETE",
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to delete universe" },
      { status: 502 },
    );
  }
}
