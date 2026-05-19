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
| 数据源 | Sina MVP，AkShare 优先增强，Tushare 可选 |

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
news_items(id, symbol, title, source, url, published_at, type)
hot_keywords(id, word, heat, sources, captured_at)
data_jobs(id, job_type, status, started_at, finished_at, error)
```

## 6. API 设计

```text
GET /api/data/health
GET /api/stocks/search?q=
GET /api/stocks/[symbol]/profile
GET /api/calendar/trading-days?start=&end=
GET /api/stock/kline/[symbol]?type=&adjust=
GET /api/stock/status/[symbol]?date=
GET /api/stock/financials/[symbol]
GET /api/data/jobs
POST /api/data/jobs/run
```

## 7. 数据质量规则

- 同一 `symbol + date + adjust_type` 不允许重复。
- 交易日历关闭日期不应出现普通日线交易数据。
- 非停牌日成交量缺失需要标记异常。
- 涨跌幅超过市场制度限制时需要标记异常。
- 每条服务化数据必须携带 `source` 或可追溯来源。

## 8. 独立测试设计

- Provider adapter 使用固定原始响应 fixture 测试解析。
- 清洗任务使用小样本数据测试去重、字段类型、缺失值处理。
- 复权计算使用已知样例测试价格连续性。
- API 层使用测试数据库，不依赖真实外部网络。
- 数据质量规则可以单独运行并输出报告。

## 9. 验收标准

- 可以查询任意 A 股最近 10 年日线数据。
- 可以区分未复权、前复权、后复权。
- 可以判断某只股票某日是否 ST、停牌、涨停、跌停。
- 数据接口稳定返回标准字段。
- 数据源异常不会污染 clean 层数据。

