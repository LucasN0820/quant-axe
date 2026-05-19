export type ChartMode = "daily" | "weekly" | "monthly" | "yearly";
export type LoadState = "idle" | "loading" | "ready" | "empty" | "error";

export type KlinePoint = {
  date: string;
  open: number;
  close: number;
  low: number;
  high: number;
  volume: number;
};

export type Quote = {
  symbol: string;
  name: string;
  current_price: number | null;
  change_rate: number | null;
  change_amount?: number | null;
  volume: number | string | null;
  turnover: number | string | null;
  high: number | null;
  low: number | null;
  open?: number | null;
  previous_close?: number | null;
  pe_ttm?: number | null;
  pb?: number | null;
  turnover_rate?: number | null;
  trade_date?: string | null;
  trade_time?: string | null;
  source?: string;
};

export type QuoteCacheEntry = {
  quote: Quote | null;
  status: LoadState | "stale";
  updatedAt: string | null;
  error: string | null;
};

export type MarketIndex = {
  symbol: string;
  name: string;
  value: number | null;
  change_rate: number | null;
};

export type StockSearchResult = {
  symbol: string;
  name: string;
  pinyin?: string;
};

export type OrderBookLevel = {
  level: string;
  price: number | null;
  volume: number | null;
};

export type OrderBookData = {
  asks: OrderBookLevel[];
  bids: OrderBookLevel[];
};

export type TradePrint = {
  time: string;
  price: number | null;
  volume: number | null;
  side: string;
};

export type NewsItem = {
  time?: string;
  source?: string;
  title: string;
  url?: string;
};

export type FinancialMetrics = {
  pe_ttm: number | null;
  pb: number | null;
  roe: number | string | null;
  gross_margin: number | string | null;
};

export type HotKeyword = {
  word: string;
  heat: number;
};

export type DetailState<T> = {
  status: LoadState;
  data: T;
  source?: string;
  message?: string;
};

