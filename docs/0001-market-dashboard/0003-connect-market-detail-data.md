# 0003 Connect Market Detail Data

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0001-market-dashboard/design.md`

## 目标

把行情看板中的占位区域逐步替换为真实数据，包括分时、五档盘口、逐笔成交、热点新闻、个股新闻、公告、财务和舆情。

## 前置依赖

- `data-center` 提供对应服务化接口。
- 行情看板已完成组件拆分。

## 执行步骤

1. 接入完整股票搜索数据源，替代本地候选池。
2. 接入 `GET /api/stock/intraday/[symbol]`，渲染真实分时图。
3. 接入 `GET /api/stock/order-book/[symbol]`，展示五档盘口。
4. 接入 `GET /api/stock/trades/[symbol]`，展示逐笔成交。
5. 接入 `GET /api/news/hot`，在独立 `/news` 页面展示全市场热点新闻。
6. 接入 `GET /api/stock/news/[symbol]` 和 `GET /api/stock/announcements/[symbol]`，区分个股新闻与公告。
7. 接入 `GET /api/stock/financials/[symbol]`，展示 PE TTM、PB、ROE、毛利率等财务摘要。
8. 接入 `GET /api/intelligence/hot-keywords`，展示全市场与个股相关热词。
9. 对所有非核心数据使用空状态，不使用 mock 结论伪装真实数据。

## 新闻接入方案

### 热点新闻

- 数据源：参考 `LucasN0820/news-collector` 项目的实现方式，使用 NewsNow 聚合 API 拉取主流平台热榜。
- 请求方式：`GET {NEWSNOW_API_BASE}/api/s?id=<platform_id>&latest`，`NEWSNOW_API_BASE` 默认可指向公开实例，后续建议支持自建 NewsNow 服务。
- 推荐平台：`cls-hot`、`wallstreetcn-hot`、`thepaper`、`baidu`、`weibo`、`zhihu`、`toutiao`。
- 标准字段：`id`、`title`、`url`、`source_id`、`source_name`、`rank`、`updated_at`、`captured_at`。
- 前端展示：热点新闻是全市场维度，不要求绑定选中股票；当前在独立 `/news` 页面展示，并通过 Dashboard 右侧边栏入口进入。列表参考 NewsNow `/c/hottest` 的来源过滤与密集信息流形态，按时间从近到远排序。

### 个股新闻

- 数据源：AkShare `stock_news_em`。
- 请求方式：按 6 位 A 股代码查询，数据中心负责把前端 `symbol` 标准化后传给 AkShare。
- 标准字段：`symbol`、`title`、`summary`、`url`、`source`、`published_at`、`captured_at`。
- 前端展示：个股新闻随 `selectedSymbol` 切换刷新，不能用热点新闻弱关联结果替代。
- 排序要求：个股新闻按 `published_at/time` 从近到远展示；热点新闻按 `updated_at/captured_at` 从近到远展示，时间缺失时保留来源内排名。

## 产出

- 真实分时、盘口、逐笔成交视图。
- 独立热点新闻页面、Dashboard 个股新闻、公告、财务、舆情视图。
- 股票搜索接入数据中心。

## 验收

- 股票切换后详情区域按选中股票刷新。
- 热点新闻与选中股票无强绑定，个股新闻按选中股票刷新。
- 数据缺失时展示空状态。
- 行情看板不再依赖主要 mock 数据。
