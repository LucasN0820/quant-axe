import type { NewsItem } from "@/lib/market-types";

export function newsTimestamp(item: NewsItem): number {
  const candidates = [
    item.published_at,
    item.time,
    item.updated_at,
    item.captured_at,
  ];

  for (const candidate of candidates) {
    const parsed = parseNewsDate(candidate);
    if (parsed !== null) {
      return parsed;
    }
  }

  return Number.NEGATIVE_INFINITY;
}

export function sortNewsByTimeDesc(items: NewsItem[]) {
  return [...items].sort((a, b) => {
    const timeDelta = newsTimestamp(b) - newsTimestamp(a);
    if (timeDelta !== 0) {
      return timeDelta;
    }
    return (a.rank ?? Infinity) - (b.rank ?? Infinity);
  });
}

export function formatNewsTime(item: NewsItem) {
  if (item.published_at || item.time || item.updated_at) {
    return item.published_at ?? item.time ?? item.updated_at ?? "--";
  }
  if (typeof item.rank === "number") {
    return `#${item.rank}`;
  }
  return item.captured_at ?? "--";
}

function parseNewsDate(value?: string) {
  if (!value) {
    return null;
  }

  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const parsed = Date.parse(normalized);
  return Number.isNaN(parsed) ? null : parsed;
}
