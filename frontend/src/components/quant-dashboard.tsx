"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  Bell,
  CandlestickChart,
  Newspaper,
  Plus,
  Search,
  Star,
  TrendingDown,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import {
  hotKeywords,
  marketIndexes,
  newsItems,
  orderBook,
  stocks,
  trades,
  type KlinePoint,
} from "@/lib/market-data";
import { KlineChart } from "@/components/kline-chart";

const STORAGE_KEY = "quantdash.watchlist.v1";
const DEFAULT_SYMBOL = "600519";

type Quote = {
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

type MarketIndex = {
  symbol: string;
  name: string;
  value: number | null;
  change_rate: number | null;
};

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function formatChange(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "--";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatNumber(value: number | string | null | undefined, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  if (typeof value === "string") {
    return value;
  }

  return value.toLocaleString("zh-CN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatAmount(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  if (typeof value === "string") {
    return value;
  }

  if (value >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(2)}亿`;
  }

  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(2)}万`;
  }

  return value.toLocaleString("zh-CN");
}

export function QuantDashboard() {
  const [query, setQuery] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState(DEFAULT_SYMBOL);
  const [watchlist, setWatchlist] = useState<string[]>(["600519", "300750", "688981"]);
  const [mode, setMode] = useState<"daily" | "weekly">("daily");
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [lookupQuote, setLookupQuote] = useState<Quote | null>(null);
  const [lookupStatus, setLookupStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle",
  );
  const [chartData, setChartData] = useState<KlinePoint[]>([]);
  const [indexes, setIndexes] = useState<MarketIndex[]>(
    marketIndexes.map((item) => ({
      symbol: item.name,
      name: item.name,
      value: Number(item.value),
      change_rate: item.change,
    })),
  );
  const [dataStatus, setDataStatus] = useState("连接 Python 行情源中");

  useEffect(() => {
    queueMicrotask(() => {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        return;
      }

      try {
        const parsed = JSON.parse(stored) as string[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setWatchlist(parsed);
          setSelectedSymbol(parsed[0]);
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    });
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
  }, [watchlist]);

  useEffect(() => {
    let active = true;

    async function loadIndexes() {
      try {
        const response = await fetch("/api/market/indexes", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`indexes ${response.status}`);
        }
        const payload = (await response.json()) as { data: MarketIndex[] };
        if (active) {
          setIndexes(payload.data);
          setDataStatus("Python 实时行情 · Sina");
        }
      } catch {
        if (active) {
          setDataStatus("行情源暂不可用，保留最近一次数据");
        }
      }
    }

    void loadIndexes();
    const timer = window.setInterval(loadIndexes, 30_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const symbol = query.replace(/\D/g, "").slice(0, 6);
    if (symbol.length !== 6) {
      queueMicrotask(() => {
        setLookupQuote(null);
        setLookupStatus("idle");
      });
      return;
    }

    let active = true;
    queueMicrotask(() => {
      if (active) {
        setLookupStatus("loading");
      }
    });
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(`/api/stock/quote/${symbol}`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`lookup ${response.status}`);
        }
        const quote = (await response.json()) as Quote;
        if (active) {
          setLookupQuote(quote);
          setLookupStatus("ready");
        }
      } catch {
        if (active) {
          setLookupQuote(null);
          setLookupStatus("error");
        }
      }
    }, 300);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [query]);

  useEffect(() => {
    let active = true;

    async function loadQuotes() {
      const results = await Promise.allSettled(
        watchlist.map(async (symbol) => {
          const response = await fetch(`/api/stock/quote/${symbol}`, { cache: "no-store" });
          if (!response.ok) {
            throw new Error(`quote ${symbol} ${response.status}`);
          }
          return [symbol, (await response.json()) as Quote] as const;
        }),
      );

      if (!active) {
        return;
      }

      setQuotes((current) => {
        const next = { ...current };
        for (const result of results) {
          if (result.status === "fulfilled") {
            next[result.value[0]] = result.value[1];
          }
        }
        return next;
      });
    }

    void loadQuotes();
    const timer = window.setInterval(loadQuotes, 10_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [watchlist]);

  useEffect(() => {
    let active = true;

    async function loadKline() {
      const response = await fetch(`/api/stock/kline/${selectedSymbol}?type=${mode}`, {
        cache: "no-store",
      });
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as { data: KlinePoint[] };
      if (active) {
        setChartData(payload.data);
      }
    }

    void loadKline();
    return () => {
      active = false;
    };
  }, [selectedSymbol, mode]);

  const selectedMeta = stocks.find((stock) => stock.symbol === selectedSymbol);
  const selectedQuote = quotes[selectedSymbol];
  const selectedPrice = selectedQuote?.current_price ?? selectedMeta?.price ?? null;
  const selectedChange = selectedQuote?.change_rate ?? selectedMeta?.changeRate ?? null;
  const valuationPe = selectedQuote?.pe_ttm ?? selectedMeta?.pe ?? null;
  const valuationPb = selectedQuote?.pb ?? selectedMeta?.pb ?? null;
  const valuationWatermark = typeof valuationPe === "number" ? Math.min(Math.round(valuationPe), 95) : 0;

  function addStock(symbol: string, quote?: Quote | null) {
    const normalized = symbol.replace(/\D/g, "").slice(0, 6);
    if (normalized.length !== 6) {
      return;
    }

    if (quote) {
      setQuotes((current) => ({ ...current, [normalized]: quote }));
    }
    setWatchlist((current) => (current.includes(normalized) ? current : [normalized, ...current]));
    setSelectedSymbol(normalized);
    setQuery("");
  }

  function removeStock(symbol: string) {
    setWatchlist((current) => {
      const next = current.filter((item) => item !== symbol);
      if (symbol === selectedSymbol) {
        setSelectedSymbol(next[0] ?? DEFAULT_SYMBOL);
      }
      return next.length > 0 ? next : [DEFAULT_SYMBOL];
    });
  }

  return (
    <main className="min-h-screen bg-[#080a0d] text-slate-100">
      <div className="flex min-h-screen flex-col xl:grid xl:grid-cols-[300px_minmax(0,1fr)_330px]">
        <aside className="border-b border-white/10 bg-[#0c1117] xl:border-b-0 xl:border-r">
          <div className="flex h-full flex-col">
            <div className="border-b border-white/10 px-5 py-5">
              <div className="flex items-center gap-3">
                <div className="grid size-10 place-items-center rounded-lg border border-emerald-400/40 bg-emerald-400/10 text-emerald-300">
                  <CandlestickChart size={21} />
                </div>
                <div>
                  <h1 className="text-lg font-semibold tracking-wide">QuantDash</h1>
                  <p className="font-mono text-xs text-slate-500">Python Market Workbench</p>
                </div>
              </div>
            </div>

            <div className="px-5 py-4">
              <label className="relative block">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="输入 6 位股票代码"
                  className="h-10 w-full rounded-md border border-white/10 bg-black/30 pl-9 pr-3 text-sm outline-none transition focus:border-emerald-400/70"
                />
              </label>

              {query && (
                <div className="mt-2 overflow-hidden rounded-md border border-white/10 bg-[#111821]">
                  {lookupStatus === "idle" && (
                    <div className="px-3 py-2 text-sm text-slate-500">输入完整 6 位 A 股代码后查询</div>
                  )}
                  {lookupStatus === "loading" && (
                    <div className="px-3 py-2 text-sm text-slate-500">正在查询真实行情</div>
                  )}
                  {lookupStatus === "error" && (
                    <div className="px-3 py-2 text-sm text-red-300">未找到该代码或行情源暂不可用</div>
                  )}
                  {lookupStatus === "ready" && lookupQuote && (
                    <button
                      type="button"
                      onClick={() => addStock(lookupQuote.symbol, lookupQuote)}
                      className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-white/5"
                    >
                      <span>
                        <span className="font-medium">{lookupQuote.name}</span>
                        <span className="ml-2 font-mono text-xs text-slate-500">
                          {lookupQuote.symbol}
                        </span>
                        <span
                          className={cn(
                            "ml-2 font-mono text-xs",
                            (lookupQuote.change_rate ?? 0) >= 0
                              ? "text-emerald-300"
                              : "text-red-300",
                          )}
                        >
                          {formatNumber(lookupQuote.current_price)} / {formatChange(lookupQuote.change_rate)}
                        </span>
                      </span>
                      <Plus size={15} className="text-emerald-300" />
                    </button>
                  )}
                </div>
              )}
            </div>

            <div className="flex-1 px-3 pb-5">
              <div className="mb-2 flex items-center justify-between px-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                <span>Watchlist</span>
                <Star size={14} />
              </div>
              <div className="space-y-2">
                {watchlist.map((symbol) => {
                  const meta = stocks.find((stock) => stock.symbol === symbol);
                  const quote = quotes[symbol];
                  const price = quote?.current_price ?? meta?.price ?? null;
                  const change = quote?.change_rate ?? meta?.changeRate ?? null;

                  return (
                    <div
                      key={symbol}
                      role="button"
                      tabIndex={0}
                      onClick={() => setSelectedSymbol(symbol)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          setSelectedSymbol(symbol);
                        }
                      }}
                      className={cn(
                        "group w-full cursor-pointer rounded-md border px-3 py-3 text-left transition",
                        selectedSymbol === symbol
                          ? "border-emerald-400/50 bg-emerald-400/10"
                          : "border-white/8 bg-white/3 hover:border-white/18 hover:bg-white/6",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="font-medium">{quote?.name ?? meta?.name ?? symbol}</div>
                          <div className="mt-1 font-mono text-xs text-slate-500">{symbol}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono text-sm">{formatNumber(price)}</div>
                          <div
                            className={cn(
                              "mt-1 font-mono text-xs",
                              (change ?? 0) >= 0 ? "text-emerald-300" : "text-red-300",
                            )}
                          >
                            {formatChange(change)}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                        <span>成交额 {formatAmount(quote?.turnover ?? meta?.turnover)}</span>
                        <span>量 {formatAmount(quote?.volume ?? meta?.volume)}</span>
                      </div>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          removeStock(symbol);
                        }}
                        className="mt-2 text-xs text-slate-600 opacity-0 transition hover:text-slate-300 group-hover:opacity-100"
                      >
                        移除
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </aside>

        <section className="min-w-0 bg-[#080a0d]">
          <header className="border-b border-white/10 bg-[#0c1117]/95 px-5 py-3 backdrop-blur">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex min-w-0 items-center gap-3 overflow-x-auto">
                {indexes.map((item) => (
                  <div key={item.name} className="flex shrink-0 items-center gap-2 rounded-md border border-white/10 bg-white/3 px-3 py-2">
                    <span className="text-sm text-slate-400">{item.name}</span>
                    <span className="font-mono text-sm">{formatNumber(item.value)}</span>
                    <span className={cn("font-mono text-xs", (item.change_rate ?? 0) >= 0 ? "text-emerald-300" : "text-red-300")}>
                      {formatChange(item.change_rate)}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Activity size={15} className="text-emerald-300" />
                <span>{dataStatus} · Quote 10s / Index 30s 轮询</span>
              </div>
            </div>
          </header>

          <div className="space-y-4 p-4 lg:p-5">
            <section className="rounded-lg border border-white/10 bg-[#0d131a]">
              <div className="flex flex-col gap-4 border-b border-white/10 px-5 py-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-semibold">
                      {selectedQuote?.name ?? selectedMeta?.name ?? selectedSymbol}
                    </h2>
                    <span className="rounded border border-white/10 px-2 py-1 font-mono text-xs text-slate-400">
                      {selectedSymbol}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-4">
                    <span className="font-mono text-3xl">{formatNumber(selectedPrice)}</span>
                    <span className={cn("flex items-center gap-1 font-mono text-sm", (selectedChange ?? 0) >= 0 ? "text-emerald-300" : "text-red-300")}>
                      {(selectedChange ?? 0) >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      {formatChange(selectedChange)}
                    </span>
                    <span className="text-sm text-slate-500">
                      H {formatNumber(selectedQuote?.high ?? selectedMeta?.high)} / L {formatNumber(selectedQuote?.low ?? selectedMeta?.low)}
                    </span>
                  </div>
                </div>
                <div className="inline-flex w-fit rounded-md border border-white/10 bg-black/25 p-1">
                  {[
                    ["daily", "日线"],
                    ["weekly", "周线"],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setMode(value as "daily" | "weekly")}
                      className={cn(
                        "rounded px-3 py-1.5 text-sm transition",
                        mode === value ? "bg-emerald-400 text-black" : "text-slate-400 hover:text-slate-100",
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-[430px] px-2 py-3">
                {chartData.length > 0 ? (
                  <KlineChart data={chartData} />
                ) : (
                  <div className="grid h-full place-items-center text-sm text-slate-500">
                    正在通过 Python 加载真实 K 线数据
                  </div>
                )}
              </div>
            </section>

            <section className="grid gap-4 lg:grid-cols-[1fr_300px]">
              <div className="rounded-lg border border-white/10 bg-[#0d131a]">
                <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
                  <Newspaper size={18} className="text-emerald-300" />
                  <h3 className="font-medium">关联新闻与实时公告</h3>
                </div>
                <div className="divide-y divide-white/10">
                  {newsItems.map((item) => (
                    <article key={`${item.time}-${item.title}`} className="grid gap-2 px-4 py-3 sm:grid-cols-[70px_92px_1fr]">
                      <time className="font-mono text-sm text-slate-500">{item.time}</time>
                      <span className="text-sm text-slate-400">{item.source}</span>
                      <h4 className="text-sm text-slate-200">{item.title}</h4>
                    </article>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-white/10 bg-[#0d131a]">
                <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
                  <BarChart3 size={18} className="text-emerald-300" />
                  <h3 className="font-medium">盘口与逐笔</h3>
                </div>
                <div className="grid grid-cols-2 gap-3 p-4 text-sm">
                  <div className="space-y-1">
                    {orderBook.asks.map(([label, price, amount]) => (
                      <div key={label} className="flex justify-between font-mono text-red-300/90">
                        <span>{label}</span><span>{price}</span><span>{amount}</span>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-1">
                    {orderBook.bids.map(([label, price, amount]) => (
                      <div key={label} className="flex justify-between font-mono text-emerald-300/90">
                        <span>{label}</span><span>{price}</span><span>{amount}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="border-t border-white/10 px-4 py-3">
                  {trades.map((trade) => (
                    <div key={`${trade.time}-${trade.price}`} className="grid grid-cols-4 gap-2 py-1 font-mono text-xs text-slate-400">
                      <span>{trade.time}</span>
                      <span className={trade.side === "买入" ? "text-red-300" : "text-emerald-300"}>{trade.price}</span>
                      <span>{trade.volume}</span>
                      <span>{trade.side}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        </section>

        <aside className="border-t border-white/10 bg-[#0c1117] xl:border-l xl:border-t-0">
          <div className="space-y-4 p-4">
            <section className="rounded-lg border border-white/10 bg-white/3">
              <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
                <WalletCards size={18} className="text-emerald-300" />
                <h3 className="font-medium">财务估值卡片</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 p-4">
                {[
                  ["PE TTM", formatNumber(valuationPe)],
                  ["PB", formatNumber(valuationPb)],
                  ["换手率", formatChange(selectedQuote?.turnover_rate)],
                  ["数据源", selectedQuote?.source ?? "loading"],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-md border border-white/10 bg-black/25 p-3">
                    <div className="text-xs text-slate-500">{label}</div>
                    <div className="mt-2 font-mono text-xl">{value}</div>
                  </div>
                ))}
              </div>
              <div className="px-4 pb-4">
                <div className="mb-2 flex justify-between text-xs text-slate-500">
                  <span>估值水位</span>
                  <span>{valuationWatermark || "--"}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-emerald-300" style={{ width: `${valuationWatermark}%` }} />
                </div>
              </div>
            </section>

            <section className="rounded-lg border border-white/10 bg-white/3">
              <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
                <Bell size={18} className="text-emerald-300" />
                <h3 className="font-medium">全网舆情热度</h3>
              </div>
              <div className="flex flex-wrap gap-2 p-4">
                {hotKeywords.map((item) => (
                  <span
                    key={item.word}
                    className="rounded-md border border-white/10 px-2.5 py-1.5 font-mono text-sm"
                    style={{
                      color: item.heat > 80 ? "#fca5a5" : item.heat > 65 ? "#fde68a" : "#8ddfcb",
                      background: `rgba(255,255,255,${item.heat / 900})`,
                      fontSize: `${12 + item.heat / 18}px`,
                    }}
                  >
                    {item.word}
                  </span>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-white/10 bg-white/3 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-medium">策略观察</h3>
                <span className="rounded bg-emerald-300/10 px-2 py-1 text-xs text-emerald-300">Real API</span>
              </div>
              <div className="space-y-3 text-sm text-slate-400">
                <p>价格、涨跌幅、指数和 K 线已由 Python 实时获取。</p>
                <p>舆情、新闻和五档逐笔仍是前端占位模块，下一步可接入爬虫服务。</p>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </main>
  );
}
