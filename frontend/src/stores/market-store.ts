import { create } from "zustand";
import { marketIndexes, type KlinePoint } from "@/lib/market-data";

export const DEFAULT_SYMBOL = "600519";
export const WATCHLIST_STORAGE_KEY = "quantdash.watchlist.v1";

export type Quote = {
  symbol: string;
  name: string;
  current_price: number | null;
  change_rate: number | null;
  volume: number | string | null;
  turnover: number | string | null;
  high: number | null;
  low: number | null;
  pe_ttm?: number | null;
  pb?: number | null;
  turnover_rate?: number | null;
  source?: string;
};

export type MarketIndex = {
  symbol: string;
  name: string;
  value: number | null;
  change_rate: number | null;
};

type LookupStatus = "idle" | "loading" | "ready" | "error";
type ChartMode = "daily" | "weekly" | "monthly" | "yearly";

type MarketStore = {
  query: string;
  selectedSymbol: string;
  watchlist: string[];
  mode: ChartMode;
  quotes: Record<string, Quote>;
  lookupQuote: Quote | null;
  lookupStatus: LookupStatus;
  chartData: KlinePoint[];
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
  mergeQuotes: (entries: Array<readonly [string, Quote]>) => void;
  setChartData: (data: KlinePoint[]) => void;
  setIndexesReady: (indexes: MarketIndex[]) => void;
  setDataUnavailable: () => void;
};

function normalizeSymbol(symbol: string) {
  return symbol.replace(/\D/g, "").slice(0, 6);
}

export const useMarketStore = create<MarketStore>((set) => ({
  query: "",
  selectedSymbol: DEFAULT_SYMBOL,
  watchlist: ["600519", "300750", "688981"],
  mode: "daily",
  quotes: {},
  lookupQuote: null,
  lookupStatus: "idle",
  chartData: [],
  indexes: marketIndexes.map((item) => ({
    symbol: item.name,
    name: item.name,
    value: Number(item.value),
    change_rate: item.change,
  })),
  dataStatus: "连接 Python 行情源中",
  setQuery: (query) => set({ query }),
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  setMode: (mode) => set({ mode }),
  hydrateWatchlist: (symbols) =>
    set({
      watchlist: symbols,
      selectedSymbol: symbols[0] ?? DEFAULT_SYMBOL,
    }),
  addStock: (symbol, quote) => {
    const normalized = normalizeSymbol(symbol);
    if (normalized.length !== 6) {
      return;
    }

    set((state) => ({
      query: "",
      selectedSymbol: normalized,
      quotes: quote ? { ...state.quotes, [normalized]: quote } : state.quotes,
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
  mergeQuotes: (entries) =>
    set((state) => {
      const quotes = { ...state.quotes };
      for (const [symbol, quote] of entries) {
        quotes[symbol] = quote;
      }
      return { quotes };
    }),
  setChartData: (chartData) => set({ chartData }),
  setIndexesReady: (indexes) =>
    set({
      indexes,
      dataStatus: "Python 实时行情 · Sina",
    }),
  setDataUnavailable: () => set({ dataStatus: "行情源暂不可用，保留最近一次数据" }),
}));
