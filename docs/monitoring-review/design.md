# Monitoring & Review 监控复盘详细设计

## 1. 模块目标

监控复盘模块负责观察系统是否正常运行，并帮助用户理解策略为什么赚钱或亏钱。它让量化系统形成闭环：运行、监控、复盘、改进。

## 2. 模块边界

### 2.1 模块内职责

- 系统健康检查。
- 数据源状态监控。
- 策略运行状态监控。
- 回测、模拟盘、实盘收益复盘。
- 每日报告生成。
- 收益归因。
- 异常告警。

### 2.2 模块外职责

- 不生成策略。
- 不清洗原始数据。
- 不执行交易。
- 不修改风控规则，只展示和告警。

## 3. 技术架构

```text
System Events / Trading Records / Portfolio Snapshots
  -> Monitoring Collector
  -> Metrics Calculator
  -> Report Generator
  -> Alert Dispatcher
  -> Review UI
```

告警渠道第一阶段可以只做页面内通知和日志，后续再接微信、钉钉或邮件。

## 4. 监控对象

| 对象 | 指标 |
| --- | --- |
| 数据源 | 最近更新时间、失败次数、延迟 |
| 策略 | 是否按时生成信号、运行耗时、错误日志 |
| 回测 | 任务状态、执行耗时、失败原因 |
| 模拟交易 | 净值、持仓、订单状态、成交状态 |
| 实盘交易 | 订单失败、撤单、成交回报、紧急停止 |
| 风控 | 拦截次数、拦截原因 |

## 5. 复盘内容

```text
今日收益
累计收益
相对基准收益
最大回撤
当前持仓
今日交易
行业暴露
个股收益贡献
交易成本影响
异常事件
策略日志
```

## 6. 数据模型

```ts
type DailyReport = {
  date: string;
  portfolio_id: string;
  daily_return: number;
  cumulative_return: number;
  benchmark_return?: number;
  max_drawdown: number;
  top_contributors: Array<{ symbol: string; contribution: number }>;
  risk_events: string[];
  generated_at: string;
};
```

```ts
type AlertEvent = {
  id: string;
  severity: "info" | "warning" | "critical";
  source: string;
  message: string;
  status: "open" | "acknowledged" | "resolved";
  created_at: string;
};
```

## 7. API 设计

```text
GET /api/monitoring/health
GET /api/monitoring/events
GET /api/reports/daily?date=
GET /api/reports/performance?portfolio_id=
GET /api/reports/attribution?portfolio_id=&date=
GET /api/alerts
POST /api/alerts/[id]/ack
POST /api/alerts/[id]/resolve
```

## 8. 独立测试设计

- 使用固定持仓和收益数据测试日报生成。
- 使用固定交易明细测试收益归因。
- 数据源超时事件应生成 warning。
- 实盘订单失败应生成 critical。
- 告警确认和关闭状态可测试。

## 9. 验收标准

- 可以查看系统健康状态。
- 可以生成每日策略报告。
- 可以看到收益、回撤、持仓、交易和异常。
- 异常事件可以形成告警并被确认。

