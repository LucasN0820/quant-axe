import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, afterEach } from "vitest";
import {
  FinancialSummaryPanel,
  HotNewsPanel,
  NewsAnnouncementPanel,
  SentimentHotwordsPanel,
} from "@/components/market-dashboard/dashboard-parts";

afterEach(() => {
  cleanup();
});

describe("dashboard empty states", () => {
  it("does not invent financial metrics when the data source is empty", () => {
    render(
      <FinancialSummaryPanel
        quote={null}
        financials={{
          status: "empty",
          data: { pe_ttm: null, pb: null, roe: null, gross_margin: null },
          source: "not_configured",
        }}
      />,
    );

    expect(screen.getByText("财务数据源尚未接入，当前不生成估值判断。")).toBeInTheDocument();
    expect(screen.getAllByText("--").length).toBeGreaterThan(0);
  });

  it("renders an empty sentiment state instead of mock hot words", () => {
    render(
      <SentimentHotwordsPanel
        hotKeywords={{ status: "empty", data: [], source: "not_configured" }}
      />,
    );

    expect(screen.getByText("舆情热词未接入")).toBeInTheDocument();
    expect(screen.queryByText("国产算力")).not.toBeInTheDocument();
  });

  it("renders hot news as a standalone global panel", () => {
    render(
      <HotNewsPanel
        hotNews={{
          status: "ready",
          data: [{ title: "市场热点", source: "CLS", rank: 1 }],
        }}
      />,
    );

    expect(screen.getByRole("heading", { level: 3, name: "热点新闻" })).toBeInTheDocument();
    expect(screen.getByText("市场热点")).toBeInTheDocument();
  });

  it("separates stock news and announcements without hot news", () => {
    render(
      <NewsAnnouncementPanel
        news={{
          status: "ready",
          data: [{ title: "个股新闻标题", source: "Eastmoney", time: "2026-04-25 10:15:22" }],
        }}
        announcements={{ status: "empty", data: [], source: "not_configured" }}
      />,
    );

    expect(screen.getByRole("heading", { level: 3, name: "个股新闻" })).toBeInTheDocument();
    expect(screen.getByText("个股新闻标题")).toBeInTheDocument();
    expect(screen.getByText("2026-04-25 10:15:22")).toHaveClass("whitespace-nowrap");
    expect(screen.getByText("公告数据未接入")).toBeInTheDocument();
    // Hot news is no longer part of this panel
    expect(screen.queryByRole("heading", { level: 3, name: "热点新闻" })).not.toBeInTheDocument();
  });

  it("shows loading and error states for connected news sources", () => {
    render(
      <NewsAnnouncementPanel
        news={{ status: "error", data: [], source: "akshare.stock_news_em", message: "AkShare timeout" }}
        announcements={{ status: "empty", data: [], source: "not_configured" }}
      />,
    );

    expect(screen.getByText("个股新闻暂不可用")).toBeInTheDocument();
    expect(screen.queryByText("个股新闻数据未接入")).not.toBeInTheDocument();
  });

  it("shows loading state for hot news panel independently", () => {
    render(
      <HotNewsPanel hotNews={{ status: "loading", data: [] }} />,
    );

    expect(screen.getByText("正在加载热点新闻")).toBeInTheDocument();
  });
});
