import { describe, expect, it } from "vitest";
import { DEFAULT_SYMBOL, useMarketStore } from "@/stores/market-store";
import type { Quote } from "@/lib/market-types";

const quote: Quote = {
  symbol: "600519",
  name: "贵州茅台",
  current_price: 1688.35,
  change_rate: 1.28,
  volume: 100,
  turnover: 1000000,
  high: 1702.2,
  low: 1659.8,
  source: "test",
};

describe("market store", () => {
  it("dedupes hydrated watchlist and selects the first valid symbol", () => {
    useMarketStore.setState({
      selectedSymbol: DEFAULT_SYMBOL,
      watchlist: [DEFAULT_SYMBOL],
      quoteCache: {},
      query: "",
    });

    useMarketStore.getState().hydrateWatchlist(["600519", "600519", "abc", "300750"]);

    expect(useMarketStore.getState().watchlist).toEqual(["600519", "300750"]);
    expect(useMarketStore.getState().selectedSymbol).toBe("600519");
  });

  it("adds quote data to cache and avoids duplicate watchlist entries", () => {
    useMarketStore.setState({
      selectedSymbol: DEFAULT_SYMBOL,
      watchlist: ["600519"],
      quoteCache: {},
      query: "600519",
    });

    useMarketStore.getState().addStock("600519", quote);

    expect(useMarketStore.getState().watchlist).toEqual(["600519"]);
    expect(useMarketStore.getState().quoteCache["600519"].quote?.name).toBe("贵州茅台");
    expect(useMarketStore.getState().query).toBe("");
  });

  it("seeds a loading quote cache entry when adding without quote data", () => {
    useMarketStore.setState({
      selectedSymbol: DEFAULT_SYMBOL,
      watchlist: ["600519"],
      quoteCache: {},
      query: "600011",
    });

    useMarketStore.getState().addStock("600011", null);

    expect(useMarketStore.getState().watchlist).toEqual(["600011", "600519"]);
    expect(useMarketStore.getState().quoteCache["600011"].status).toBe("loading");
    expect(useMarketStore.getState().quoteCache["600011"].quote).toBeNull();
  });

  it("marks failed quote refreshes as stale when old data exists", () => {
    useMarketStore.setState({
      quoteCache: {
        "600519": {
          quote,
          status: "ready",
          updatedAt: "2026-05-19T00:00:00.000Z",
          error: null,
        },
      },
    });

    useMarketStore.getState().mergeQuoteResults([], ["600519"]);

    expect(useMarketStore.getState().quoteCache["600519"].status).toBe("stale");
    expect(useMarketStore.getState().quoteCache["600519"].quote?.symbol).toBe("600519");
  });
});
