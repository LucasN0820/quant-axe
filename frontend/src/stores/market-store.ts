import { create } from "zustand";
import type { ChartMode, KlinePoint, MarketIndex, Quote, QuoteCacheEntry } from "@/lib/market-types";

export const DEFAULT_SYMBOL = "600519";
export const WATCHLIST_STORAGE_KEY = "quantdash.watchlist.v1";

type LookupStatus = "idle" | "loading" | "ready" | "error";

type MarketStore = {
  query: string;
  selectedSymbol: string;
  watchlist: string[];
  mode: ChartMode;
  quoteCache: Record<string, QuoteCacheEntry>;
  lookupQuote: Quote | null;
  lookupStatus: LookupStatus;
  chartData: KlinePoint[];
  chartStatus: "idle" | "loading" | "ready" | "error";
  indexes: MarketIndex[];
  dataStatus: string;
  setQuery: (query: string) => void;
  setSelectedSymbol: (symbol: string) => void;
  setMode: (mode: ChartMode) => void;
  hydrateWatchlist: (symbols: string[]) => void;
  addStock: (symbol: string, quote?: Quote | null) => void;
  removeStock: (symbol: string) => void;
  setLookupIdle: () => void;
  setLookupLoading: () => void;
  setLookupReady: (quote: Quote) => void;
  setLookupError: () => void;
  markQuotesLoading: (symbols: string[]) => void;
  mergeQuoteResults: (entries: Array<readonly [string, Quote]>, failedSymbols?: string[]) => void;
  setChartLoading: () => void;
  setChartData: (data: KlinePoint[]) => void;
  setChartError: () => void;
  setIndexesReady: (indexes: MarketIndex[]) => void;
  setDataUnavailable: () => void;
};

function normalizeSymbol(symbol: string) {
  return symbol.replace(/\D/g, "").slice(0, 6);
}

function dedupeSymbols(symbols: string[]) {
  return Array.from(new Set(symbols.map(normalizeSymbol).filter((symbol) => symbol.length === 6)));
}

function cacheEntry(quote: Quote): QuoteCacheEntry {
  return {
    quote,
    status: "ready",
    updatedAt: new Date().toISOString(),
    error: null,
  };
}

const initialIndexes: MarketIndex[] = [
  { symbol: "000001", name: "上证指数", value: null, change_rate: null },
  { symbol: "399001", name: "深证成指", value: null, change_rate: null },
  { symbol: "399006", name: "创业板指", value: null, change_rate: null },
  { symbol: "000688", name: "科创50", value: null, change_rate: null },
];

export const useMarketStore = create<MarketStore>((set) => ({
  query: "",
  selectedSymbol: DEFAULT_SYMBOL,
  watchlist: ["600519", "300750", "688981"],
  mode: "daily",
  quoteCache: {},
  lookupQuote: null,
  lookupStatus: "idle",
  chartData: [],
  chartStatus: "idle",
  indexes: initialIndexes,
  dataStatus: "连接 Python 行情源中",
  setQuery: (query) => set({ query }),
  setSelectedSymbol: (symbol) => {
    const normalized = normalizeSymbol(symbol);
    if (normalized.length === 6) {
      set({ selectedSymbol: normalized });
    }
  },
  setMode: (mode) => set({ mode }),
  hydrateWatchlist: (symbols) =>
    set((state) => {
      const watchlist = dedupeSymbols(symbols);
      return {
        watchlist: watchlist.length > 0 ? watchlist : state.watchlist,
        selectedSymbol: watchlist[0] ?? state.selectedSymbol,
      };
    }),
  addStock: (symbol, quote) => {
    const normalized = normalizeSymbol(symbol);
    if (normalized.length !== 6) {
      return;
    }

    set((state) => ({
      query: "",
      selectedSymbol: normalized,
      lookupQuote: null,
      lookupStatus: "idle",
      quoteCache: quote
        ? { ...state.quoteCache, [normalized]: cacheEntry({ ...quote, symbol: normalized }) }
        : state.quoteCache,
      watchlist: state.watchlist.includes(normalized)
        ? state.watchlist
        : [normalized, ...state.watchlist],
    }));
  },
  removeStock: (symbol) =>
    set((state) => {
      const next = state.watchlist.filter((item) => item !== symbol);
      const watchlist = next.length > 0 ? next : [DEFAULT_SYMBOL];
      return {
        watchlist,
        selectedSymbol: symbol === state.selectedSymbol ? watchlist[0] : state.selectedSymbol,
      };
    }),
  setLookupIdle: () => set({ lookupQuote: null, lookupStatus: "idle" }),
  setLookupLoading: () => set({ lookupStatus: "loading" }),
  setLookupReady: (quote) => set({ lookupQuote: quote, lookupStatus: "ready" }),
  setLookupError: () => set({ lookupQuote: null, lookupStatus: "error" }),
  markQuotesLoading: (symbols) =>
    set((state) => {
      const quoteCache = { ...state.quoteCache };
      for (const symbol of dedupeSymbols(symbols)) {
        const current = quoteCache[symbol];
        quoteCache[symbol] = {
          quote: current?.quote ?? null,
          status: current?.quote ? "stale" : "loading",
          updatedAt: current?.updatedAt ?? null,
          error: null,
        };
      }
      return { quoteCache };
    }),
  mergeQuoteResults: (entries, failedSymbols = []) =>
    set((state) => {
      const quoteCache = { ...state.quoteCache };
      for (const [symbol, quote] of entries) {
        quoteCache[symbol] = cacheEntry(quote);
      }
      for (const symbol of dedupeSymbols(failedSymbols)) {
        const current = quoteCache[symbol];
        quoteCache[symbol] = {
          quote: current?.quote ?? null,
          status: current?.quote ? "stale" : "error",
          updatedAt: current?.updatedAt ?? null,
          error: "行情源暂不可用",
        };
      }
      return { quoteCache };
    }),
  setChartLoading: () => set({ chartStatus: "loading" }),
  setChartData: (chartData) => set({ chartData, chartStatus: chartData.length > 0 ? "ready" : "idle" }),
  setChartError: () => set({ chartStatus: "error" }),
  setIndexesReady: (indexes) =>
    set({
      indexes,
      dataStatus: "Python 实时行情 · Sina",
    }),
  setDataUnavailable: () => set({ dataStatus: "行情源暂不可用，保留最近一次数据" }),
}));
