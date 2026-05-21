"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowLeft,
  ExternalLink,
  Flame,
  Newspaper,
  Radio,
  RefreshCw,
} from "lucide-react";
import { useHotNews } from "@/components/market-dashboard/use-market-dashboard-data";
import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/market-format";
import type { NewsItem } from "@/lib/market-types";
import { formatNewsTime, newsTimestamp, sortNewsByTimeDesc } from "@/lib/news-utils";

type SourceOption = {
  id: string;
  name: string;
  count: number;
};

export function NewsPage() {
  const hotNews = useHotNews(120);
  const [activeSource, setActiveSource] = useState("all");

  const sortedNews = useMemo(() => sortNewsByTimeDesc(hotNews.data), [hotNews.data]);
  const sources = useMemo(() => sourceOptions(sortedNews), [sortedNews]);
  const visibleNews = useMemo(
    () =>
      activeSource === "all"
        ? sortedNews
        : sortedNews.filter((item) => sourceId(item) === activeSource),
    [activeSource, sortedNews],
  );
  const lastUpdated = useMemo(() => latestTimeLabel(sortedNews), [sortedNews]);

  return (
    <main className="min-h-screen bg-[#080a0d] text-slate-100">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-[#0c1117]/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 lg:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/"
              className="grid size-9 place-items-center rounded-md border border-white/10 text-slate-400 transition hover:border-emerald-300/50 hover:text-emerald-200"
              aria-label="返回 Dashboard"
            >
              <ArrowLeft size={18} />
            </Link>
            <div className="grid size-10 place-items-center rounded-md border border-emerald-400/40 bg-emerald-400/10 text-emerald-300">
              <Newspaper size={21} />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold">QuantDash News</h1>
              <p className="truncate text-xs text-slate-500">全市场热点新闻流</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <span className="hidden rounded-md border border-white/10 px-3 py-2 text-xs text-slate-500 sm:inline">
              {lastUpdated ? `更新 ${lastUpdated}` : "等待数据"}
            </span>
            <ThemeToggle />
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="grid size-9 place-items-center rounded-md border border-white/10 text-slate-400 transition hover:border-emerald-300/50 hover:text-emerald-200"
              aria-label="刷新新闻"
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:grid-cols-[220px_minmax(0,1fr)] lg:px-6">
        <aside className="lg:sticky lg:top-[76px] lg:self-start">
          <section className="rounded-lg border border-white/10 bg-[#0d131a]">
            <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
              <Flame size={17} className="text-emerald-300" />
              <h2 className="font-medium">来源</h2>
            </div>
            <div className="space-y-1 p-2">
              <SourceButton
                label="全部热点"
                count={sortedNews.length}
                active={activeSource === "all"}
                onClick={() => setActiveSource("all")}
              />
              {sources.map((source) => (
                <SourceButton
                  key={source.id}
                  label={source.name}
                  count={source.count}
                  active={activeSource === source.id}
                  onClick={() => setActiveSource(source.id)}
                />
              ))}
            </div>
          </section>
        </aside>

        <section className="min-w-0 rounded-lg border border-white/10 bg-[#0d131a]">
          <div className="flex flex-col gap-3 border-b border-white/10 px-4 py-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm text-emerald-300">
                <Radio size={16} />
                <span>Hottest</span>
              </div>
              <h2 className="mt-1 text-2xl font-semibold">热点新闻</h2>
            </div>
            <div className="text-sm text-slate-500">
              {hotNews.status === "loading" && sortedNews.length === 0
                ? "正在同步 NewsNow"
                : `${visibleNews.length} 条新闻`}
            </div>
          </div>

          {visibleNews.length > 0 ? (
            <ol className="divide-y divide-white/10">
              {visibleNews.map((item, index) => (
                <NewsRow key={`${sourceId(item)}-${item.rank ?? index}-${item.title}`} item={item} index={index} />
              ))}
            </ol>
          ) : (
            <div className="p-5">
              <div className="rounded-md border border-white/10 bg-black/20 p-4 text-sm">
                <div className="font-medium text-slate-300">
                  {hotNews.status === "error" ? "热点新闻暂不可用" : "正在加载热点新闻"}
                </div>
                <p className="mt-2 text-slate-500">
                  {hotNews.message ?? "数据来自 NewsNow 聚合接口，加载完成后会按时间从近到远展示。"}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function SourceButton({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition",
        active ? "bg-emerald-300 text-black" : "text-slate-400 hover:bg-white/5 hover:text-slate-100",
      )}
    >
      <span className="truncate">{label}</span>
      <span className={cn("ml-3 font-mono text-xs", active ? "text-black/70" : "text-slate-600")}>{count}</span>
    </button>
  );
}

function NewsRow({ item, index }: { item: NewsItem; index: number }) {
  const source = item.source_name ?? item.source ?? sourceId(item);
  const href = item.url || item.mobile_url;

  return (
    <li className="grid gap-3 px-4 py-4 transition hover:bg-white/3 md:grid-cols-[3rem_minmax(0,1fr)_150px] md:items-start">
      <div className="font-mono text-xl text-slate-600">{String(index + 1).padStart(2, "0")}</div>
      <div className="min-w-0">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="rounded border border-white/10 px-2 py-1 text-xs text-slate-500">{source}</span>
          {typeof item.rank === "number" && (
            <span className="rounded bg-emerald-300/10 px-2 py-1 font-mono text-xs text-emerald-300">
              #{item.rank}
            </span>
          )}
        </div>
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="group inline-flex max-w-full items-start gap-2 text-base font-medium text-slate-100 transition hover:text-emerald-300"
          >
            <span className="min-w-0">{item.title}</span>
            <ExternalLink size={15} className="mt-1 shrink-0 opacity-0 transition group-hover:opacity-100" />
          </a>
        ) : (
          <h3 className="text-base font-medium text-slate-100">{item.title}</h3>
        )}
        {item.summary && <p className="mt-2 line-clamp-2 text-sm text-slate-500">{item.summary}</p>}
      </div>
      <time className="whitespace-nowrap font-mono text-sm text-slate-500 md:text-right">{formatNewsTime(item)}</time>
    </li>
  );
}

function sourceOptions(items: NewsItem[]) {
  const bySource = new Map<string, SourceOption>();
  for (const item of items) {
    const id = sourceId(item);
    const current = bySource.get(id);
    bySource.set(id, {
      id,
      name: item.source_name ?? item.source ?? id,
      count: (current?.count ?? 0) + 1,
    });
  }
  return Array.from(bySource.values()).sort((a, b) => b.count - a.count);
}

function sourceId(item: NewsItem) {
  return item.source_id ?? item.source ?? "unknown";
}

function latestTimeLabel(items: NewsItem[]) {
  const timestamp = Math.max(...items.map(newsTimestamp));
  if (!Number.isFinite(timestamp)) {
    return "";
  }
  return new Date(timestamp).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
