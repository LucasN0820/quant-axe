# 0004 Build Alternative And Display Data

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0002-data-center/design.md`

## 目标

补齐行情看板和后续情绪、价值因子所需的财务、热点新闻、个股新闻、公告、舆情、分时、盘口和逐笔成交数据。

## 前置依赖

- 数据源 adapter 已建立。
- 核心股票资料可查询。

## 执行步骤

1. 建立 `financial_metrics`，记录 PE TTM、PB、ROE、毛利率、报告期和来源。
2. 建立 `hot_news_items`，记录 NewsNow 热点新闻的来源平台、排名、标题、链接、更新时间和采集时间。
3. 建立 `news_items`，区分个股新闻、公告、财报、回购、减持、增持等类型。
4. 建立 `hot_keywords`，记录热词、热度、来源和采集时间。
5. 参考 `LucasN0820/news-collector` 的实现方式接入 NewsNow 热点新闻：按平台 ID 请求 `GET /api/s?id=<platform_id>&latest`，标准化为 `GET /api/news/hot`。
6. 使用 AkShare `stock_news_em` 接入个股新闻，标准化为 `GET /api/stock/news/[symbol]`。
7. 使用 Tushare `anns` 接入真实公告，标准化为 `GET /api/stock/announcements/[symbol]`。
8. 使用 Tushare `daily_basic` + `fina_indicator` 接入真实财务指标，标准化为 `GET /api/stock/financials/[symbol]`。
9. 接入真实分时图数据接口：AkShare `stock_zh_a_hist_min_em` 主源，`stock_zh_a_minute` 备选。
10. 接入真实五档盘口数据接口。
11. 接入真实逐笔成交数据接口：第一版使用 AkShare `stock_intraday_em` 当日分笔聚合。
12. 为热点新闻、个股新闻、公告、财务和舆情任务设计分钟、小时或财报周期更新频率。
13. 对数据缺失保留空结果，不生成投资结论。

## 新闻源策略

- 热点新闻：使用 NewsNow 聚合 API 作为 MVP 数据源，优先平台为 `cls-hot`、`wallstreetcn-hot`、`thepaper`、`baidu`、`weibo`、`zhihu`、`toutiao`。该数据只代表全市场热点，不直接绑定股票。
- 个股新闻：使用 AkShare `stock_news_em`，按 6 位 A 股代码查询东方财富个股新闻。该数据随选中股票刷新，是行情看板个股新闻区域的主数据源。
- 公告：不使用 NewsNow 替代公告，第一版使用 Tushare `anns`，后续可补充交易所或巨潮源。
- 财务指标：使用 Tushare `daily_basic` + `fina_indicator` 合并估值、质量、成长和市值字段；未配置 `TUSHARE_TOKEN` 时返回 `not_configured`。
- 舆情热词：第一版从 NewsNow 热点新闻标题中做关键词统计，后续再引入更完整的热度、情绪或 NLP 分析。

## 产出

- 财务指标数据。
- 热点新闻、个股新闻、公告数据。
- 舆情热词数据。
- 分时、盘口、逐笔成交接口。

## 验收

- 行情看板可以移除主要 mock 新闻、盘口、舆情和财务数据。
- 热点新闻和个股新闻来源不同、接口不同、字段类型清晰。
- 财务和舆情数据包含来源与更新时间。
- 数据缺失不会导致接口异常。
