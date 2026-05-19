# 0004 Risk API And Tests

来源：`docs/0008-risk-center/design.md`、`docs/0008-risk-center/progress.md`

## 目标

提供统一风控接口，并补齐风控规则测试。

## 前置依赖

- 仓位类和交易状态类规则已完成。

## 执行步骤

1. 实现 `POST /api/risk/check-order`。
2. 实现 `POST /api/risk/check-portfolio`。
3. 实现 `GET /api/risk/limits`。
4. 实现 `PATCH /api/risk/limits`。
5. 实现 `GET /api/risk/events`。
6. 测试超过单票上限的订单被阻塞。
7. 测试停牌股票订单被阻塞。
8. 测试涨停买入和跌停卖出被阻塞。
9. 测试数据缺失行情被阻塞。
10. 测试风控规则不依赖 UI 可单独运行。

## 产出

- 风控检查接口。
- 风控规则配置接口。
- 风控事件查询接口。
- 风控单元测试。

## 验收

- 所有交易前都能调用风控检查。
- 回测、模拟交易和实盘交易复用同一套规则。
- 风控规则可单独测试。

