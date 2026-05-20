import { NextResponse } from "next/server";
import { fetchMarketData } from "@/lib/python-market";

export async function GET(request: Request) {
  const { search } = new URL(request.url);

  try {
    const data = await fetchMarketData(`/api/news/hot${search}`);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "failed to fetch hot news", data: [] },
      { status: 502 },
    );
  }
}
