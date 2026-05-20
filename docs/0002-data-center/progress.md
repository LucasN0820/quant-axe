# Data Center 数据中心实现进展

## 已完成

- [x] FastAPI 数据服务骨架。
- [x] Data Center API 骨架：`/api/data/health`、`/api/data/jobs`、`/api/data/jobs/run`。
- [x] AkShare quote 适配。
- [x] AkShare 指数适配。
- [x] AkShare 日 K 数据适配。
- [x] K 线接口支持 `adjust=none|qfq|hfq`，并保留日/周/月/年聚合。
- [x] AkShare 五档盘口适配。
- [x] 周线、月线、年线后端聚合。
- [x] Next.js BFF 转发行情请求。
- [x] NewsNow 热点新闻适配。
- [x] AkShare 个股新闻适配。
- [x] 新闻接口统一按可解析时间倒序返回，时间缺失时保留来源排名。
- [x] PostgreSQL 本地存储层接入，使用 `POSTGRES_DSN`，包含 raw、clean、adjusted、news、job 等基础表 schema。
- [x] Redis 本地缓存层接入，使用 `REDIS_URL`，用于 K 线等 serving 数据 JSON 缓存。
- [x] Tushare 外部数据源接入，使用 `TUSHARE_TOKEN`，当前覆盖股票基础信息与公告入口。
- [x] 股票基础信息查询接口：`/api/stocks/{symbol}/profile` 与 `/api/stocks/profiles`。
- [x] 交易日历接口：`/api/calendar/trading-days`。
- [x] 股票状态接口：`/api/stock/status/{symbol}`，可返回 ST、停牌、涨跌停价格与涨跌停触发状态。
- [x] 数据质量规则与接口：`/api/data/quality/daily-bars/{symbol}`。
- [x] 后端单元测试：数据质量规则、交易所识别、涨跌停比例、日期标准化。

## 待完成

- [x] 接入 AkShare 数据源。
- [x] 建立股票基础信息数据表。
- [x] 建立交易日历。
- [x] 建立 ST 状态数据。
- [x] 建立停牌数据。
- [x] 建立涨跌停价格数据。
- [x] 建立前复权/后复权行情。
- [ ] 建立财务指标数据。
- [x] 建立热点新闻入库存储。
- [x] 建立个股新闻公告入库存储。
- [ ] 建立舆情热词数据。
- [x] 增加 PostgreSQL 存储。
- [x] 增加 Redis 缓存。
- [x] 增加数据更新任务入口与 `data_jobs` 记录表。
- [x] 增加数据质量检查。
- [x] 增加后端单元测试。
- [ ] 增加完整调度器，自动按日/小时/财报周期触发更新任务。

## 阻塞/待确认

- [x] 历史行情数据源优先使用 AkShare 还是申请 Tushare Token：行情继续优先 AkShare，Tushare 作为公告和基础资料补充源。
- [x] 热点新闻是否使用公开 NewsNow 实例作为 MVP，或优先自建 NewsNow 服务：MVP 使用可配置 `NEWSNOW_API_BASE`，默认公开实例。
- [ ] 历史行情是否使用 Parquet/DuckDB 存储。
- [ ] 本地运行需配置 PostgreSQL、Redis 服务和 `TUSHARE_TOKEN`；代码已接入，环境值不提交到仓库。
