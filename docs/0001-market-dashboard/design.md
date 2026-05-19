# Market Dashboard 行情看板详细设计

## 1. 模块目标

行情看板负责让用户快速理解市场状态，是 QuantDash 的入口模块。它聚合自选股、实时 quote、市场指数、K 线、新闻公告、舆情热词与财务摘要，但不负责策略计算、回测、组合构建或实盘下单。

## 2. 模块边界

### 2.1 模块内职责

- 自选股搜索、添加、删除、选中。
- 展示自选股实时行情快照。
- 展示主要市场指数。
- 展示个股 K 线、成交量、均线。
- 展示新闻、公告、舆情、财务指标的摘要视图。
- 处理行情源异常时的前端降级展示。

### 2.2 模块外职责

- 数据清洗与历史数据存储由 `data-center` 负责。
- 股票池过滤由 `universe-center` 负责。
- 因子计算由 `factor-engine` 负责。
- 策略、回测、组合、风控、交易不在本模块内实现。

## 3. 技术架构

```text
React UI
  -> Zustand dashboard state
  -> Next.js Route Handlers
  -> FastAPI market/data services
  -> Redis cache / external data source
```

前端建议组件拆分：

```text
MarketDashboardPage
  WatchlistPanel
  MarketIndexTicker
  StockHeader
  KlinePanel
  NewsAnnouncementPanel
  OrderBookPanel
  FinancialSummaryPanel
  SentimentHotwordsPanel
```

## 4. 数据模型

```ts
type Quote = {
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
  trade_date?: string | null;
  trade_time?: string | null;
  source?: string;
};
```

```ts
type KlinePoint = {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
};
```

```ts
type WatchlistState = {
  query: string;
  selectedSymbol: string;
  watchlist: string[];
  quotes: Record<string, Quote>;
  chartMode: "daily" | "weekly" | "monthly" | "yearly";
};
```

## 5. API 依赖

| Endpoint | 来源模块 | 用途 |
| --- | --- | --- |
| `GET /api/market/indexes` | data-center | 顶部指数栏 |
| `GET /api/stock/quote/[symbol]` | data-center | 自选股和主面板行情 |
| `GET /api/stock/kline/[symbol]` | data-center | K 线图 |
| `GET /api/stock/intraday/[symbol]` | data-center | 分时图 |
| `GET /api/stock/order-book/[symbol]` | data-center | 五档盘口 |
| `GET /api/stock/trades/[symbol]` | data-center | 逐笔成交 |
| `GET /api/stock/news/[symbol]` | data-center | 新闻流 |
| `GET /api/stock/announcements/[symbol]` | data-center | 公告流 |
| `GET /api/intelligence/hot-keywords` | data-center | 舆情热词 |

## 6. 关键流程

### 6.1 添加自选股

```text
输入代码/名称/拼音
  -> 本地候选匹配
  -> 如果是 6 位代码，发起 quote 查询
  -> 用户点击添加
  -> 更新 watchlist
  -> 持久化 localStorage
  -> 设为 selectedSymbol
```

### 6.2 切换股票

```text
点击自选股
  -> 更新 selectedSymbol
  -> 读取/刷新 quote
  -> 请求 K 线
  -> 触发新闻、公告、财务、舆情摘要刷新
```

## 7. 独立测试设计

- Mock BFF 接口，独立测试 UI 组件，不依赖真实行情源。
- 自选股添加、删除、去重、选中逻辑使用 store 单元测试。
- K 线组件传入固定 `KlinePoint[]`，验证图表容器正常渲染。
- quote 接口失败时，页面展示降级状态，不白屏。
- `localStorage` 损坏数据时自动恢复默认列表。

## 8. 验收标准

- 用户能通过 6 位代码添加股票。
- 用户能看到自选股 quote、涨跌颜色、成交额。
- 用户能切换日/周/月/年 K 线。
- 行情源失败时保留最近一次数据或展示空状态。
- 新闻、舆情、财务没有真实数据时不伪造结论。

