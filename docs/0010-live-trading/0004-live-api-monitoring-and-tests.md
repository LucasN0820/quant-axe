# 0004 Live API Monitoring And Tests

来源：`docs/0010-live-trading/design.md`、`docs/0010-live-trading/progress.md`

## 目标

提供实盘 API，接入监控复盘，并用 mock broker 完成集成测试。

## 前置依赖

- 实盘订单流程已完成。
- `monitoring-review` 事件和告警能力可用。

## 执行步骤

1. 实现 `GET /api/live/accounts`。
2. 实现 `GET /api/live/positions`。
3. 实现 `POST /api/live/orders/preview`。
4. 实现 `POST /api/live/orders/confirm`。
5. 实现 `POST /api/live/orders/cancel`。
6. 实现 `GET /api/live/executions`。
7. 实现 `GET /api/live/audit-logs`。
8. 实现 `POST /api/live/emergency-stop`。
9. 将实盘订单失败写入告警。
10. 将实盘成交写入审计和复盘报告。
11. 增加 mock broker 集成测试。

## 产出

- 实盘交易 API。
- 实盘监控事件。
- mock broker 集成测试。

## 验收

- 所有交易操作可追溯。
- 实盘失败能生成告警。
- mock broker 下能完整跑通账户、预览、确认、成交和撤单。

