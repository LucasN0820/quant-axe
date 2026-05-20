# Data Center 数据中心详细设计

## 1. 模块目标

数据中心负责 QuantDash 的所有基础数据采集、清洗、存储、质量检查和服务化输出。它是行情看板、股票池、因子、策略、回测、组合、风控和交易模块的共同地基。

## 2. 模块边界

### 2.1 模块内职责

- 外部数据源适配。
- 原始数据保存。
- 字段标准化和数据清洗。
- 复权价格生成。
- 交易日历、停牌、ST、涨跌停数据维护。
- 财务、新闻、公告、舆情数据入库。
- 为其他模块提供稳定查询接口。

### 2.2 模块外职责

- 不决定策略买卖逻辑。
- 不负责因子组合、策略回测、交易下单。
- 不在数据层做投资建议。

## 3. 技术架构

```text
External Sources
  -> Provider Adapters
  -> Raw Storage
  -> Cleaning Jobs
  -> Clean Tables / Parquet
  -> Feature-ready Serving API
```

建议技术栈：

| 层级 | 技术 |
| --- | --- |
| API | FastAPI |
| 批处理 | Pandas / Polars |
| 任务调度 | APScheduler / Celery / Prefect |
| 关系数据 | PostgreSQL |
| 历史行情/因子矩阵 | Parquet / DuckDB |
| 高频缓存 | Redis |
| 数据源 | AkShare 行情与个股新闻，NewsNow 热点新闻，Tushare 可选 |

## 4. 数据分层

```text
raw
  保存外部源原始响应，便于追溯

clean
  标准字段、标准类型、标准交易日

adjusted
  前复权、后复权、未复权行情

feature
  可供因子和策略读取的特征宽表

serving
  面向前端、回测和策略的稳定接口
```

## 5. 核心数据表

```text
stock_profiles(symbol, name, exchange, industry, listed_at, delisted_at, pinyin)
trade_calendar(date, is_open, exchange)
daily_bars(symbol, date, open, high, low, close, volume, turnover, adjust_type)
limit_prices(symbol, date, up_limit, down_limit)
stock_status(symbol, date, is_st, is_suspended)
financial_metrics(symbol, report_period, pe_ttm, pb, roe, gross_margin, source)
news_items(id, symbol, title, summary, source, url, published_at, type)
hot_news_items(id, source_id, source_name, rank, title, url, updated_at, captured_at)
hot_keywords(id, word, heat, sources, captured_at)
data_jobs(id, job_type, status, started_at, finished_at, error)
```

新闻数据分层：

- `hot_news_items` 保存全市场热点新闻。数据源参考 `news-collector` 的 NewsNow 聚合 API 方式，按平台 ID 拉取热榜，适合构建市场级舆情和热词，不直接作为个股新闻。
- `news_items` 保存个股新闻、公告、财报、回购、减持、增持等与股票强相关的数据。第一版个股新闻使用 AkShare `stock_news_em`，公告后续可接 Tushare 或交易所/巨潮源。

## 6. API 设计

```text
GET /api/data/health
GET /api/stocks/search?q=
GET /api/stocks/[symbol]/profile
GET /api/calendar/trading-days?start=&end=
GET /api/stock/kline/[symbol]?type=&adjust=
GET /api/stock/status/[symbol]?date=
GET /api/stock/financials/[symbol]
GET /api/news/hot?sources=&limit=
GET /api/stock/news/[symbol]?limit=
GET /api/stock/announcements/[symbol]?limit=
GET /api/intelligence/hot-keywords?symbol=
GET /api/data/jobs
POST /api/data/jobs/run
```

## 7. 新闻与舆情 Provider 设计

### 7.1 NewsNow 热点新闻 Provider

- 用途：全市场热点新闻和舆情热词输入。
- 参考实现：`LucasN0820/news-collector` 的 `DataFetcher`，请求 `GET /api/s?id=<platform_id>&latest`。
- 配置项：`NEWSNOW_API_BASE`、启用的平台 ID 列表、请求间隔、超时、重试次数。
- 推荐平台：`cls-hot`、`wallstreetcn-hot`、`thepaper`、`baidu`、`weibo`、`zhihu`、`toutiao`。
- 清洗规则：跳过空标题；保留来源、排名、URL、更新时间；同一 `source_id + title` 在同一抓取批次去重。
- 风险控制：公开 NewsNow 实例只作为 MVP 数据源，后续应允许切换到自建 NewsNow 服务，避免依赖第三方公开实例稳定性。

### 7.2 AkShare 个股新闻 Provider

- 用途：按 `symbol` 查询个股新闻，服务 `GET /api/stock/news/[symbol]`。
- 接口：AkShare `stock_news_em`。
- 清洗规则：标准化 6 位 A 股代码；输出标题、摘要、来源、链接、发布时间和抓取时间；缺少发布时间时保留空值，不伪造时间。
- 降级策略：AkShare 请求失败或无数据时返回空列表和 `status: unavailable` 或 `status: empty`，不生成 mock 新闻。

## 8. 数据质量规则

- 同一 `symbol + date + adjust_type` 不允许重复。
- 交易日历关闭日期不应出现普通日线交易数据。
- 非停牌日成交量缺失需要标记异常。
- 涨跌幅超过市场制度限制时需要标记异常。
- 每条服务化数据必须携带 `source` 或可追溯来源。
- 热点新闻与个股新闻分表或分类型存储，不能把全市场热榜直接标记为个股新闻。
- 新闻 URL 为空时允许用 `source + title + captured_at` 做临时去重键，但需要标记不可追溯风险。

## 9. 独立测试设计

- Provider adapter 使用固定原始响应 fixture 测试解析。
- 清洗任务使用小样本数据测试去重、字段类型、缺失值处理。
- 复权计算使用已知样例测试价格连续性。
- API 层使用测试数据库，不依赖真实外部网络。
- 数据质量规则可以单独运行并输出报告。

## 10. 验收标准

- 可以查询任意 A 股最近 10 年日线数据。
- 可以区分未复权、前复权、后复权。
- 可以判断某只股票某日是否 ST、停牌、涨停、跌停。
- 可以查询全市场热点新闻和指定股票的个股新闻，且二者来源和类型清晰区分。
- 数据接口稳定返回标准字段。
- 数据源异常不会污染 clean 层数据。
