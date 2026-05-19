# 0003 Connect Market Detail Data

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0001-market-dashboard/design.md`

## 目标

把行情看板中的占位区域逐步替换为真实数据，包括分时、五档盘口、逐笔成交、新闻、公告、财务和舆情。

## 前置依赖

- `data-center` 提供对应服务化接口。
- 行情看板已完成组件拆分。

## 执行步骤

1. 接入完整股票搜索数据源，替代本地候选池。
2. 接入 `GET /api/stock/intraday/[symbol]`，渲染真实分时图。
3. 接入 `GET /api/stock/order-book/[symbol]`，展示五档盘口。
4. 接入 `GET /api/stock/trades/[symbol]`，展示逐笔成交。
5. 接入 `GET /api/stock/news/[symbol]` 和 `GET /api/stock/announcements/[symbol]`，区分新闻与公告。
6. 接入 `GET /api/stock/financials/[symbol]`，展示 PE TTM、PB、ROE、毛利率等财务摘要。
7. 接入 `GET /api/intelligence/hot-keywords`，展示全市场与个股相关热词。
8. 对所有非核心数据使用空状态，不使用 mock 结论伪装真实数据。

## 产出

- 真实分时、盘口、逐笔成交视图。
- 真实新闻、公告、财务、舆情视图。
- 股票搜索接入数据中心。

## 验收

- 股票切换后详情区域按选中股票刷新。
- 数据缺失时展示空状态。
- 行情看板不再依赖主要 mock 数据。

