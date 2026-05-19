# 0001 Refactor Dashboard Shell

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0001-market-dashboard/design.md`

## 目标

拆分行情看板主页面，降低主组件复杂度，为后续真实新闻、盘口、财务和舆情接入预留稳定组件边界。

## 前置依赖

- 已有 Next.js App Router 页面骨架。
- 已有 Zustand 行情状态。
- 已有三栏行情工作台布局。

## 执行步骤

1. 梳理现有行情看板页面中的自选股、指数、K 线、新闻公告、盘口、财务和舆情区域。
2. 拆出 `WatchlistPanel`、`MarketIndexTicker`、`StockHeader`、`KlinePanel`、`NewsAnnouncementPanel`、`OrderBookPanel`、`FinancialSummaryPanel`、`SentimentHotwordsPanel`。
3. 保留 `MarketDashboardPage` 只负责布局编排、选中股票传递和页面级加载状态。
4. 将自选股增删、选中、去重和 `localStorage` 恢复逻辑收敛到 store 或独立 hook。
5. 为每个组件定义清晰 props，避免组件直接访问无关全局状态。
6. 补齐行情源失败、空数据、加载中三类状态的统一展示。

## 产出

- 行情看板组件拆分完成。
- 主页面只保留页面布局和模块组合逻辑。
- 组件级状态边界清晰。

## 验收

- 现有自选股、指数、K 线功能不回退。
- 行情接口失败时页面不白屏。
- `localStorage` 损坏数据时能恢复默认列表或空列表。

