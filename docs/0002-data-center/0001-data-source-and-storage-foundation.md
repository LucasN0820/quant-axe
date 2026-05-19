# 0001 Data Source And Storage Foundation

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0002-data-center/design.md`

## 目标

建立数据中心的外部数据源、存储和任务基础设施，让后续股票池、因子和回测不依赖临时行情接口。

## 前置依赖

- 已有 FastAPI 数据服务骨架。
- 已有 Sina quote、指数、日 K 和周期聚合。
- 待确认 AkShare 与 Tushare 的优先级。

## 执行步骤

1. 定义 provider adapter 接口，统一外部数据源返回结构和错误格式。
2. 接入 AkShare 作为研究与回测优先数据源。
3. 保留 Sina 作为 MVP 行情展示和降级来源。
4. 评估 Tushare Token 接入成本，若未确认则保留 adapter 占位。
5. 建立 PostgreSQL 连接、迁移方案和基础表管理流程。
6. 评估历史行情、因子矩阵是否使用 Parquet/DuckDB，并记录结论。
7. 增加 Redis 缓存，用于 quote、盘口、分时和任务状态。
8. 设计 `data_jobs` 任务表，记录任务状态、开始结束时间和错误信息。

## 产出

- 数据源 adapter 边界。
- PostgreSQL 基础存储。
- Redis 缓存入口。
- 数据更新任务记录模型。

## 验收

- 数据中心能从统一接口调用 Sina 和 AkShare。
- 数据任务状态可查询。
- 外部数据源失败不会污染 clean 层。

