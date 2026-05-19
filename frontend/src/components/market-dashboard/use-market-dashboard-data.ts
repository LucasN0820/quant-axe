"use client";

import { useEffect, useMemo, useState } from "react";
import { WATCHLIST_STORAGE_KEY, useMarketStore } from "@/stores/market-store";
import type {
  DetailState,
  FinancialMetrics,
  HotKeyword,
  KlinePoint,
  MarketIndex,
  NewsItem,
  OrderBookData,
  Quote,
  StockSearchResult,
  TradePrint,
} from "@/lib/market-types";

const QUOTE_POLL_INTERVAL_MS = 10_000;
const INDEX_POLL_INTERVAL_MS = 30_000;

function emptyState<T>(data: T): DetailState<T> {
  return { status: "idle", data };
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} ${response.status}`);
  }
  return (await response.json()) as T;
}

export function useWatchlistPersistence() {
  const hydrateWatchlist = useMarketStore((state) => state.hydrateWatchlist);
  const watchlist = useMarketStore((state) => state.watchlist);

  useEffect(() => {
    const stored = window.localStorage.getItem(WATCHLIST_STORAGE_KEY);
    if (!stored) {
      return;
    }

    try {
      const parsed = JSON.parse(stored) as string[];
      if (Array.isArray(parsed)) {
        hydrateWatchlist(parsed);
      }
    } catch {
      window.localStorage.removeItem(WATCHLIST_STORAGE_KEY);
    }
  }, [hydrateWatchlist]);

  useEffect(() => {
    window.localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist));
  }, [watchlist]);
}

export function useMarketIndexes() {
  const setIndexesReady = useMarketStore((state) => state.setIndexesReady);
  const setDataUnavailable = useMarketStore((state) => state.setDataUnavailable);

  useEffect(() => {
    let active = true;

    async function loadIndexes() {
      try {
        const payload = await fetchJson<{ data: MarketIndex[] }>("/api/market/indexes");
        if (active) {
          setIndexesReady(payload.data);
        }
      } catch {
        if (active) {
          setDataUnavailable();
        }
      }
    }

    void loadIndexes();
    const timer = window.setInterval(loadIndexes, INDEX_POLL_INTERVAL_MS);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [setDataUnavailable, setIndexesReady]);
}

export function useStockLookup(query: string) {
  const setLookupIdle = useMarketStore((state) => state.setLookupIdle);
  const setLookupLoading = useMarketStore((state) => state.setLookupLoading);
  const setLookupReady = useMarketStore((state) => state.setLookupReady);
  const setLookupError = useMarketStore((state) => state.setLookupError);
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [searchStatus, setSearchStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");

  useEffect(() => {
    const text = query.trim();
    const symbol = text.replace(/\D/g, "").slice(0, 6);
    let active = true;

    if (!text) {
      queueMicrotask(() => {
        if (active) {
          setResults([]);
          setSearchStatus("idle");
          setLookupIdle();
        }
      });
      return;
    }

    const timer = window.setTimeout(async () => {
      setSearchStatus("loading");
      try {
        const payload = await fetchJson<{ data: StockSearchResult[] }>(
          `/api/stocks/search?q=${encodeURIComponent(text)}`,
        );
        if (active) {
          setResults(payload.data ?? []);
          setSearchStatus("ready");
        }
      } catch {
        if (active) {
          setResults([]);
          setSearchStatus("error");
        }
      }
    }, 180);

    if (symbol.length !== 6) {
      setLookupIdle();
      return () => {
        active = false;
        window.clearTimeout(timer);
      };
    }

    setLookupLoading();
    const quoteTimer = window.setTimeout(async () => {
      try {
        const quote = await fetchJson<Quote>(`/api/stock/quote/${symbol}`);
        if (active) {
          setLookupReady(quote);
        }
      } catch {
        if (active) {
          setLookupError();
        }
      }
    }, 260);

    return () => {
      active = false;
      window.clearTimeout(timer);
      window.clearTimeout(quoteTimer);
    };
  }, [query, setLookupError, setLookupIdle, setLookupLoading, setLookupReady]);

  return { results, searchStatus };
}

export function useQuotePolling() {
  const selectedSymbol = useMarketStore((state) => state.selectedSymbol);
  const watchlist = useMarketStore((state) => state.watchlist);
  const markQuotesLoading = useMarketStore((state) => state.markQuotesLoading);
  const mergeQuoteResults = useMarketStore((state) => state.mergeQuoteResults);

  const symbols = useMemo(
    () => Array.from(new Set([selectedSymbol, ...watchlist])),
    [selectedSymbol, watchlist],
  );

  useEffect(() => {
    let active = true;

    async function loadQuotes() {
      markQuotesLoading(symbols);
      const results = await Promise.allSettled(
        symbols.map(async (symbol) => {
          const quote = await fetchJson<Quote>(`/api/stock/quote/${symbol}`);
          return [symbol, quote] as const;
        }),
      );

      if (!active) {
        return;
      }

      const entries: Array<readonly [string, Quote]> = [];
      const failedSymbols: string[] = [];
      for (let index = 0; index < results.length; index += 1) {
        const result = results[index];
        const symbol = symbols[index];
        if (result.status === "fulfilled") {
          entries.push(result.value);
        } else {
          failedSymbols.push(symbol);
        }
      }
      mergeQuoteResults(entries, failedSymbols);
    }

    void loadQuotes();
    const timer = window.setInterval(loadQuotes, QUOTE_POLL_INTERVAL_MS);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [markQuotesLoading, mergeQuoteResults, symbols]);
}

export function useKlineData() {
  const selectedSymbol = useMarketStore((state) => state.selectedSymbol);
  const mode = useMarketStore((state) => state.mode);
  const setChartLoading = useMarketStore((state) => state.setChartLoading);
  const setChartData = useMarketStore((state) => state.setChartData);
  const setChartError = useMarketStore((state) => state.setChartError);

  useEffect(() => {
    let active = true;

    async function loadKline() {
      setChartLoading();
      try {
        const payload = await fetchJson<{ data: KlinePoint[] }>(
          `/api/stock/kline/${selectedSymbol}?type=${mode}`,
        );
        if (active) {
          setChartData(payload.data ?? []);
        }
      } catch {
        if (active) {
          setChartError();
        }
      }
    }

    void loadKline();
    return () => {
      active = false;
    };
  }, [mode, selectedSymbol, setChartData, setChartError, setChartLoading]);
}

export function useMarketDetails(symbol: string) {
  const [orderBook, setOrderBook] = useState<DetailState<OrderBookData>>(emptyState({ asks: [], bids: [] }));
  const [trades, setTrades] = useState<DetailState<TradePrint[]>>(emptyState([]));
  const [news, setNews] = useState<DetailState<NewsItem[]>>(emptyState([]));
  const [announcements, setAnnouncements] = useState<DetailState<NewsItem[]>>(emptyState([]));
  const [financials, setFinancials] = useState<DetailState<FinancialMetrics>>(
    emptyState({ pe_ttm: null, pb: null, roe: null, gross_margin: null }),
  );
  const [hotKeywords, setHotKeywords] = useState<DetailState<HotKeyword[]>>(emptyState([]));

  useEffect(() => {
    let active = true;

    async function loadDetails() {
      setOrderBook({ status: "loading", data: { asks: [], bids: [] } });
      setTrades({ status: "loading", data: [] });
      setNews({ status: "loading", data: [] });
      setAnnouncements({ status: "loading", data: [] });
      setFinancials({ status: "loading", data: { pe_ttm: null, pb: null, roe: null, gross_margin: null } });
      setHotKeywords({ status: "loading", data: [] });

      const [
        orderBookResult,
        tradesResult,
        newsResult,
        announcementsResult,
        financialsResult,
        hotKeywordsResult,
      ] = await Promise.allSettled([
        fetchJson<{ data: OrderBookData; source?: string }>(`/api/stock/order-book/${symbol}`),
        fetchJson<{ data: TradePrint[]; source?: string }>(`/api/stock/trades/${symbol}`),
        fetchJson<{ data: NewsItem[]; source?: string }>(`/api/stock/news/${symbol}`),
        fetchJson<{ data: NewsItem[]; source?: string }>(`/api/stock/announcements/${symbol}`),
        fetchJson<{ data: FinancialMetrics; source?: string }>(`/api/stock/financials/${symbol}`),
        fetchJson<{ data: HotKeyword[]; source?: string }>("/api/intelligence/hot-keywords"),
      ]);

      if (!active) {
        return;
      }

      setOrderBook(toObjectState(orderBookResult, { asks: [], bids: [] }));
      setTrades(toArrayState(tradesResult));
      setNews(toArrayState(newsResult));
      setAnnouncements(toArrayState(announcementsResult));
      setFinancials(
        toObjectState(financialsResult, { pe_ttm: null, pb: null, roe: null, gross_margin: null }),
      );
      setHotKeywords(toArrayState(hotKeywordsResult));
    }

    void loadDetails();
    return () => {
      active = false;
    };
  }, [symbol]);

  return { orderBook, trades, news, announcements, financials, hotKeywords };
}

function toArrayState<T>(
  result: PromiseSettledResult<{ data: T[]; source?: string }>,
): DetailState<T[]> {
  if (result.status === "rejected") {
    return { status: "error", data: [], message: "数据接口暂不可用" };
  }
  return {
    status: result.value.data.length > 0 ? "ready" : "empty",
    data: result.value.data,
    source: result.value.source,
  };
}

function toObjectState<T>(
  result: PromiseSettledResult<{ data: T; source?: string }>,
  fallback: T,
): DetailState<T> {
  if (result.status === "rejected") {
    return { status: "error", data: fallback, message: "数据接口暂不可用" };
  }
  return {
    status: "ready",
    data: result.value.data ?? fallback,
    source: result.value.source,
  };
}
