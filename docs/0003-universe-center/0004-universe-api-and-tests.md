# 0004 Universe API And Tests

来源：`docs/0003-universe-center/design.md`、`docs/0003-universe-center/progress.md`

## 目标

提供股票池管理、预览、快照和历史读取接口，并补齐过滤器测试。

## 前置依赖

- 股票池模型、基础池和过滤器管道已完成。

## 执行步骤

1. 实现 `GET /api/universes`。
2. 实现 `POST /api/universes`。
3. 实现 `GET /api/universes/[id]`。
4. 实现 `PATCH /api/universes/[id]` 和 `DELETE /api/universes/[id]`。
5. 实现 `POST /api/universes/[id]/preview`，返回指定日期的模拟成分和剔除原因。
6. 实现 `POST /api/universes/[id]/snapshot`，保存指定交易日快照。
7. 实现 `GET /api/universes/[id]/stocks?date=YYYY-MM-DD`。
8. 使用小样本为每个过滤器补齐单元测试。

## 产出

- 股票池 CRUD 接口。
- 股票池预览接口。
- 股票池历史快照接口。
- 过滤器测试。

## 验收

- 用户可以查看任意交易日股票池成分。
- 回测读取历史股票池时不出现未来函数。
- 同一配置重复生成结果一致。

