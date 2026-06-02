# News Center R2 + A 股时间线 AI 分析改造

## 1. 目标

热点新闻不再由 QuantDash 直接请求公开 NewsNow 实例，而是读取
`news-collector` 定时上传到 Cloudflare R2 的 SQLite 快照。个股新闻和个股
公告继续由 AkShare 实时获取。

News Center 在三个财经平台热榜之上增加 AI 分析。分析任务在 QuantDash
后台执行，按沪深 A 股交易时间线调度，不阻塞页面请求。

## 2. 数据流

```text
news-collector GitHub Actions
  -> Cloudflare R2: news/YYYY-MM-DD.db
  -> QuantDash 每 5 分钟 HEAD 检查 ETag
  -> ETag 变化后下载并解析 SQLite
  -> /api/news/hot 展示财经平台热榜
  -> A 股时间线触发 AI 分析
  -> PostgreSQL 保存分析历史和运行记录
  -> /api/news/analysis/latest 展示最近成功分析
```

首版仅展示：

- `cls-hot`
- `wallstreetcn-hot`
- `ifeng`

## 3. R2 快照读取

R2 provider 使用 S3 兼容 API 读取 `news/YYYY-MM-DD.db`，下载后使用只读
SQLite 连接解析并清理临时文件。

- `current`：读取最新一条 `crawl_records.crawl_time`，仅返回
  `news_items.last_crawl_time` 与它相同的当前榜单。
- `daily`：读取快照中当日全部条目，并附带 `crawl_count` 和
  `rank_history`，用于 AI 汇总分析。
- 页面读取优先使用进程内缓存。每 5 分钟执行一次 `HEAD` 检查，只有 ETag
  变化才重新下载。
- 当天对象缺失、损坏或不可读时，按日期倒序读取最近可用对象，响应标记
  `stale: true`、`snapshot_date` 和 `snapshot_crawl_time`。

## 4. A 股 AI 时间线

调度器使用 `backend/config/news_ai_timeline.yaml`。交易日优先读取
PostgreSQL `trade_calendar`；当日缺失时尝试通过 AkShare 刷新；仍失败时
按周一至周五临时降级，并标记 `calendar_degraded: true`。

### 4.1 交易日

| 节点 | 时间 | 模式 | 用途 |
| --- | --- | --- | --- |
| `pre_market` | `09:20` | `daily` | 隔夜与盘前消息 |
| `morning_session` | `10:00/10:30/11:00/11:30` | `current` | 上午盘中热点 |
| `midday_summary` | `12:00` | `daily` | 午间阶段汇总 |
| `afternoon_session` | `13:30/14:00/14:30/15:00` | `current` | 下午盘中热点 |
| `closing_summary` | `15:30` | `daily` | 收盘复盘 |
| `evening_summary` | `18:30` | `daily` | 盘后财经热点 |

### 4.2 休市日

| 节点 | 时间 | 模式 |
| --- | --- | --- |
| `non_trading_morning` | `09:30` | `daily` |
| `non_trading_evening` | `18:30` | `daily` |

APScheduler 每分钟检查当前是否命中时间线节点。使用日期、节点和计划时间
作为运行记录唯一键，避免服务重启后重复执行。命中节点但
`snapshot_key + ETag + analysis_mode` 已分析时，记录
`skipped_unchanged_snapshot`，不重复调用模型。

## 5. AI 分析

AI service 使用 LiteLLM。提示词参考 `news-collector`，但只保留适合量化
News Center 的内容：

- 输入三个财经平台的标题、排名、抓取次数和排名轨迹。
- `ai_interests.txt` 用于引导模型优先识别关注方向，不裁剪热榜。
- 输出固定为 `core_trends`、`sentiment_controversy`、`signals`、
  `outlook_strategy` 四区。
- 首版不接 RSS、不接翻译、不提供页面手动生成按钮。

页面请求不调用模型。没有成功分析时，AI 区返回 `waiting` 状态。

## 6. 持久化

新增 PostgreSQL 表：

```text
hot_news_ai_analyses
  id, snapshot_key, snapshot_etag, snapshot_date, snapshot_crawl_time,
  node_key, analysis_mode, model, content, analyzed_news, generated_at

hot_news_ai_analysis_runs
  id, execution_date, node_key, scheduled_time, analysis_mode, status,
  snapshot_key, snapshot_etag, calendar_degraded, error, started_at, finished_at
```

分析历史只追加成功结果。页面首版只读取最近一条成功分析。

## 7. API

保留并扩展：

```text
GET /api/news/hot?sources=&limit=
```

响应包含：

```text
source: news_collector.r2
status
snapshot_date
snapshot_crawl_time
stale
source_status
data[]
```

新增：

```text
GET /api/news/analysis/latest
```

无成功记录时返回 `status: waiting`。存在记录时返回四区分析、节点、模式、
生成时间、关联快照和 `stale` 状态。

## 8. 环境变量

```text
NEWS_R2_ENDPOINT_URL=
NEWS_R2_BUCKET_NAME=
NEWS_R2_ACCESS_KEY_ID=
NEWS_R2_SECRET_ACCESS_KEY=
NEWS_R2_REGION=
NEWS_R2_PREFIX=news
NEWS_R2_CACHE_TTL_SECONDS=300
HOT_NEWS_SOURCES=cls-hot,wallstreetcn-hot,ifeng
AI_ANALYSIS_ENABLED=false
AI_ANALYSIS_TIMELINE_PATH=backend/config/news_ai_timeline.yaml
AI_ANALYSIS_MAX_NEWS=150
AI_MODEL=deepseek/deepseek-v4-flash
AI_API_KEY=
AI_API_BASE=
AI_TIMEOUT_SECONDS=120
AI_TEMPERATURE=1.0
AI_MAX_TOKENS=5000
AI_NUM_RETRIES=1
```

## 9. 降级规则

- R2 不可用：回退最近成功快照；完全没有快照时热点接口返回
  `unavailable`。
- AI 未配置或调用失败：热点列表照常展示，AI 区展示最近成功分析或
  `waiting`。
- 交易日历不可用：临时按工作日判断，调度状态显示降级标记。
- ETag 未变化：记录跳过原因，不重复生成相同模式报告。

