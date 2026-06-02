export type ChartMode = "1min" | "5day" | "daily" | "weekly" | "monthly" | "yearly";
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
  kind?: "stock" | "index" | "etf";
  exchange?: string;
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
  turnover?: number | null;
  side: string;
};

export type NewsItem = {
  time?: string;
  source?: string;
  source_id?: string;
  source_name?: string;
  title: string;
  url?: string;
  mobile_url?: string;
  summary?: string;
  rank?: number;
  published_at?: string;
  updated_at?: string;
  captured_at?: string;
  first_crawl_time?: string;
  last_crawl_time?: string;
  crawl_count?: number;
  rank_timeline?: Array<{ time: string; rank: number | null }>;
};

export type NewsAnalysis = {
  core_trends: string;
  sentiment_controversy: string;
  signals: string;
  outlook_strategy: string;
  node_key: string;
  analysis_mode: "current" | "daily";
  model: string;
  snapshot_date: string;
  snapshot_crawl_time: string;
  generated_at: string;
  analyzed_news: number;
};

export type NewsAnalysisState = {
  status: "loading" | "ready" | "waiting" | "error";
  data: NewsAnalysis | null;
  stale?: boolean;
  message?: string;
};

export type FinancialMetrics = {
  pe_ttm: number | null;
  pe?: number | null;
  pb: number | null;
  ps_ttm?: number | null;
  dv_ttm?: number | null;
  roe: number | string | null;
  roe_waa?: number | null;
  gross_margin: number | string | null;
  netprofit_margin?: number | null;
  debt_to_assets?: number | null;
  revenue_yoy?: number | null;
  netprofit_yoy?: number | null;
  turnover_rate?: number | null;
  total_mv?: number | null;
  circ_mv?: number | null;
  trade_date?: string | null;
  report_period?: string | null;
};

export type HotKeyword = {
  word: string;
  heat: number;
  frequency?: number;
  sources?: string[];
};

export type DetailState<T> = {
  status: LoadState;
  data: T;
  source?: string;
  message?: string;
};
