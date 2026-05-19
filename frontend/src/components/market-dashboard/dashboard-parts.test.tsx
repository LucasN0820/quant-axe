import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  FinancialSummaryPanel,
  SentimentHotwordsPanel,
} from "@/components/market-dashboard/dashboard-parts";

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
});

