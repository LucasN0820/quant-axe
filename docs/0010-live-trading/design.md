# Live Trading 实盘交易详细设计

## 1. 模块目标

实盘交易模块负责连接真实券商账户，完成资金同步、持仓同步、订单预览、人工确认下单、撤单、成交回报和审计日志。该模块是最后阶段能力，默认不启用全自动交易。

## 2. 模块边界

### 2.1 模块内职责

- 券商接口适配。
- 实盘账户资金和持仓同步。
- 建议订单预览。
- 人工确认后下单。
- 撤单。
- 成交回报同步。
- 紧急停止。
- 交易审计日志。

### 2.2 模块外职责

- 不负责策略生成。
- 不负责回测。
- 不负责模拟交易。
- 不绕过风控。
- 不默认执行全自动下单。

## 3. 技术架构

```text
Rebalance Plan
  -> Risk Check
  -> Live Order Preview
  -> Human Confirmation
  -> Broker Adapter
  -> Execution Report
  -> Audit Log
```

券商适配层必须隔离：

```text
BrokerAdapter
  get_account()
  get_positions()
  preview_order()
  place_order()
  cancel_order()
  get_executions()
```

## 4. 安全原则

- 实盘默认关闭，需要显式启用。
- 下单前必须经过风控检查。
- 第一版必须人工确认，不做全自动下单。
- 必须支持紧急停止。
- 必须记录每次预览、确认、下单、撤单、成交和失败。
- 敏感凭证不进入前端，不写入代码仓库。

## 5. 数据模型

```ts
type LiveOrderPreview = {
  id: string;
  account_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  estimated_price: number;
  estimated_value: number;
  risk_result: RiskCheckResult;
  status: "preview" | "confirmed" | "expired" | "rejected";
};
```

```ts
type LiveExecution = {
  broker_order_id: string;
  symbol: string;
  side: "buy" | "sell";
  filled_quantity: number;
  filled_price: number;
  fee: number;
  executed_at: string;
};
```

## 6. API 设计

```text
GET /api/live/accounts
GET /api/live/positions
POST /api/live/orders/preview
POST /api/live/orders/confirm
POST /api/live/orders/cancel
GET /api/live/executions
GET /api/live/audit-logs
POST /api/live/emergency-stop
```

## 7. 独立测试设计

- 使用 mock broker adapter 测试，不连接真实券商。
- 风控失败时不能生成可确认订单。
- 未人工确认的订单不能下发。
- 紧急停止后所有新订单被拒绝。
- 券商返回失败时记录审计日志。
- 成交回报能正确同步到本地记录。

## 8. 验收标准

- 实盘订单下发前必须通过风控。
- 实盘订单下发前必须人工确认。
- 所有交易操作可追溯。
- 紧急停止能够阻止后续下单。
- 模块可以在 mock broker 下完整测试。

