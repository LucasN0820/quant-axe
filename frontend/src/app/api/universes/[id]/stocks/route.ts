import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const { search } = new URL(request.url);

  try {
    const data = await fetchMarketData(`/api/universes/${id}/stocks${search}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch universe stocks" },
      { status: 502 },
    );
  }
}
