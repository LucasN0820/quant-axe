# 0005 Monitoring API And Tests

来源：`docs/0011-monitoring-review/design.md`、`docs/0011-monitoring-review/progress.md`

## 目标

提供监控复盘 API，并补齐日报、归因和告警测试。

## 前置依赖

- 健康监控、日报、归因和告警已完成。

## 执行步骤

1. 实现 `GET /api/monitoring/health`。
2. 实现 `GET /api/monitoring/events`。
3. 实现 `GET /api/reports/daily?date=`。
4. 实现 `GET /api/reports/performance?portfolio_id=`。
5. 实现 `GET /api/reports/attribution?portfolio_id=&date=`。
6. 实现 `GET /api/alerts`。
7. 实现 `POST /api/alerts/[id]/ack`。
8. 实现 `POST /api/alerts/[id]/resolve`。
9. 使用固定持仓和收益数据测试日报生成。
10. 使用固定交易明细测试收益归因。
11. 测试告警确认和关闭状态。

## 产出

- 监控复盘 API。
- 日报和归因测试。
- 告警状态测试。

## 验收

- 可以查看系统健康状态。
- 可以查询每日策略报告和收益归因。
- 异常事件可以形成告警并被确认。

