# 0004 Strategy API And Tests

来源：`docs/0005-research-lab/design.md`、`docs/0005-research-lab/progress.md`

## 目标

提供策略管理和信号查询接口，并补齐策略单元测试。

## 前置依赖

- 策略模型、运行时和模板已完成。

## 执行步骤

1. 实现 `GET /api/strategies`。
2. 实现 `POST /api/strategies`。
3. 实现 `GET /api/strategies/[id]`。
4. 实现 `PATCH /api/strategies/[id]`，参数变化时生成新版本。
5. 实现 `POST /api/strategies/[id]/preview-signals`。
6. 实现 `GET /api/strategies/[id]/signals?date=YYYY-MM-DD`。
7. 使用固定股票池和固定因子值测试策略输出。
8. 测试信号持久化和版本绑定。

## 产出

- 策略 CRUD 接口。
- 信号预览和查询接口。
- 策略单元测试。

## 验收

- 策略能在指定日期输出买入或卖出信号。
- 回测可以绑定策略版本和参数。
- 策略输出可解释且可复现。

