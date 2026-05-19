# 0004 Paper API And Tests

来源：`docs/0009-paper-trading/design.md`、`docs/0009-paper-trading/progress.md`

## 目标

提供模拟交易 API，并补齐虚拟账户、订单、成交、净值和风控测试。

## 前置依赖

- 订单流、成交模拟器和账本已完成。

## 执行步骤

1. 实现 `POST /api/paper/accounts`。
2. 实现 `GET /api/paper/accounts/[id]`。
3. 实现 `GET /api/paper/accounts/[id]/positions`。
4. 实现 `POST /api/paper/orders`。
5. 实现 `GET /api/paper/orders`。
6. 实现 `POST /api/paper/orders/[id]/cancel`。
7. 实现 `GET /api/paper/equity-curve`。
8. 实现 `GET /api/paper/logs`。
9. 测试账户创建后现金等于初始资金。
10. 测试成交、手续费、滑点、风控拒绝和净值曲线。

## 产出

- 模拟交易 API。
- 模拟交易单元测试。
- 连续运行记录能力。

## 验收

- 可以提交模拟订单并更新虚拟持仓。
- 模拟盘可连续运行并记录每日状态。
- 模拟盘至少连续运行 1-3 个月后再考虑实盘。

