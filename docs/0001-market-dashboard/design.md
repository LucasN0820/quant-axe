# Market Dashboard 行情看板详细设计

## 1. 模块目标

行情看板负责让用户快速理解市场状态，是 QuantDash 的入口模块。它聚合自选股、实时 quote、市场指数、K 线、个股新闻、公告、舆情热词与财务摘要，并提供进入独立 News page 的入口；热点新闻在独立 News page 承载，不挤占股票 K 线主工作区。

## 2. 模块边界

### 2.1 模块内职责

- 自选股搜索、添加、删除、选中。
- 展示自选股实时行情快照。
- 展示主要市场指数。
- 展示个股 K 线、成交量、均线。
- 展示个股新闻、公告、舆情、财务指标的摘要视图，并在右侧边栏提供热点新闻入口。
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
  StockNewsAnnouncementPanel
  OrderBookPanel
  NewsCenterEntryPanel
  FinancialSummaryPanel
  SentimentHotwordsPanel
NewsPage
  NewsSourceSidebar
  HotNewsFeed
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
| `GET /api/stocks/search` | data-center | 自选股搜索，覆盖 A 股、指数、ETF、拼音和拼音首字母 |
| `GET /api/market/indexes` | data-center | 顶部指数栏 |
| `GET /api/stock/quote/[symbol]` | data-center | 自选股和主面板行情 |
| `GET /api/stock/kline/[symbol]` | data-center | K 线图 |
| `GET /api/stock/intraday/[symbol]` | data-center | 分时图 |
| `GET /api/stock/order-book/[symbol]` | data-center | 五档盘口 |
| `GET /api/stock/trades/[symbol]` | data-center | 逐笔成交 |
| `GET /api/news/hot` | data-center | News page 热点新闻流，参考 `news-collector` 的 NewsNow 聚合 API 方式接入 |
| `GET /api/stock/news/[symbol]` | data-center | 个股新闻流，使用 AkShare 个股新闻接口接入 |
| `GET /api/stock/announcements/[symbol]` | data-center | 公告流，使用 Tushare `anns` |
| `GET /api/stock/financials/[symbol]` | data-center | 财务摘要，使用 Tushare `daily_basic` + `fina_indicator` |
| `GET /api/intelligence/hot-keywords` | data-center | 舆情热词，基于 NewsNow 标题派生 |

### 5.1 新闻数据分层

新闻在产品展示中分为两类：

- 热点新闻：面向全市场，在 `/news` 独立页面展示当前主流平台的财经、宏观、产业和交易相关热点。Dashboard 右侧边栏只保留入口，不在 K 线主工作区展示热点列表。数据中心参考 `LucasN0820/news-collector` 的实现方式，通过 NewsNow 聚合 API 按平台 ID 拉取热榜，不直接逐站解析今日头条、微博、知乎、财联社、澎湃等页面。
- 个股新闻：面向选中股票，在 Dashboard 详情区展示该股票相关的新闻流。数据中心使用 AkShare `stock_news_em` 接入东方财富个股新闻，并按 `symbol` 标准化返回。

热点新闻优先支持以下 NewsNow 平台 ID：

```text
cls-hot           财联社热门
wallstreetcn-hot  华尔街见闻
thepaper          澎湃新闻
baidu             百度热搜
weibo             微博
zhihu             知乎
toutiao           今日头条
```

热点新闻不等同于公告，也不承担个股精确关联。若需要在个股页展示“相关热点”，前端只能基于股票名称、简称、行业或关键词做弱关联标记，不能替代 `GET /api/stock/news/[symbol]`。

新闻展示统一按可解析时间从近到远排序：优先 `published_at/time`，其次 `updated_at/captured_at`，时间缺失时保留来源排名。新闻时间戳列必须保持不换行，避免在窄屏或侧栏中拆成多行。

### 5.2 非新闻数据源分工

- 实时 quote、市场指数、K 线、分时、五档盘口和逐笔成交由 AkShare 提供；分时图以 `stock_zh_a_hist_min_em` 为主源，逐笔成交第一版使用 `stock_intraday_em` 当日分笔聚合。
- 股票搜索由 `data-center` 构建跨标的搜索索引，覆盖 A 股（沪/深/北）、重要指数、ETF，并支持代码、名称、拼音和拼音首字母。
- 公告和财务指标由 Tushare 提供；未配置 `TUSHARE_TOKEN` 时前端展示空状态，不生成模拟结论。

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
  -> 触发个股新闻、公告、财务、舆情摘要刷新
```

### 6.3 News page 热点新闻刷新

```text
进入 /news 或定时刷新
  -> 请求 GET /api/news/hot
  -> data-center 依次拉取配置的平台热榜
  -> 标准化 title/url/source/rank/updated_at
  -> 返回全市场热点新闻列表
  -> 前端按时间倒序展示，并支持按来源过滤
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
- 热点新闻与个股新闻在展示和接口上明确区分：热点新闻在 `/news`，个股新闻在 Dashboard。
- 新闻、舆情、财务没有真实数据时不伪造结论。
