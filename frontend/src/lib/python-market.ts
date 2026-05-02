export async function fetchMarketData<T>(path: string): Promise<T> {
  const baseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8000";

  const response = await fetch(`${baseUrl}${path}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(12_000),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`market api ${response.status}: ${message}`);
  }

  return (await response.json()) as T;
}
