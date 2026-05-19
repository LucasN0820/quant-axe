# Paper Trading 模拟交易详细设计

## 1. 模块目标

模拟交易使用真实行情和虚拟资金运行策略，用来验证策略在实时环境中的稳定性。它是回测和实盘之间的缓冲层，实盘前必须先经过模拟交易。

## 2. 模块边界

### 2.1 模块内职责

- 管理虚拟账户。
- 管理模拟订单。
- 模拟成交。
- 更新虚拟现金、持仓和净值。
- 保存每日交易、持仓、净值和策略日志。

### 2.2 模块外职责

- 不生成策略信号。
- 不负责历史回测。
- 不连接真实券商。
- 不做真实资金交易。

## 3. 技术架构

```text
Strategy Signal
  -> Portfolio Target
  -> Risk Check
  -> Paper Order
  -> Fill Simulator
  -> Virtual Account Ledger
  -> Daily Equity Curve
```

模拟交易可以复用回测中的账户账本、手续费、滑点和风控规则，但输入数据使用实时或准实时行情。

## 4. 数据模型

```ts
type PaperAccount = {
  id: string;
  name: string;
  initial_cash: number;
  cash: number;
  total_value: number;
  created_at: string;
};
```

```ts
type PaperOrder = {
  id: string;
  account_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  order_price?: number;
  status: "pending" | "filled" | "partial_filled" | "cancelled" | "rejected";
  created_at: string;
};
```

```ts
type PaperPosition = {
  account_id: string;
  symbol: string;
  quantity: number;
  cost_basis: number;
  market_value: number;
  unrealized_pnl: number;
};
```

## 5. 成交流程

```text
策略生成信号
  -> 组合模块生成目标持仓
  -> 风控模块检查订单
  -> 创建模拟订单
  -> 使用 quote 或下一个 bar 模拟成交
  -> 扣除手续费和滑点
  -> 更新现金和持仓
  -> 记录净值
```

## 6. 成交模型

第一版支持两种模式：

- `next_open`：使用下一个交易日开盘价成交，适合日频策略。
- `quote_snapshot`：使用当前 quote 快照成交，适合盘中模拟。

成交模型必须明确记录，避免复盘时混淆。

## 7. API 设计

```text
POST /api/paper/accounts
GET /api/paper/accounts/[id]
GET /api/paper/accounts/[id]/positions
POST /api/paper/orders
GET /api/paper/orders
POST /api/paper/orders/[id]/cancel
GET /api/paper/equity-curve
GET /api/paper/logs
```

## 8. 独立测试设计

- 创建虚拟账户后现金等于初始资金。
- 买入成交后现金减少、持仓增加。
- 卖出成交后现金增加、持仓减少。
- 手续费和滑点正确扣除。
- 风控拒绝的订单不会进入成交。
- 净值曲线根据现金和持仓市值计算。

## 9. 验收标准

- 可以创建虚拟账户。
- 可以提交模拟订单并更新虚拟持仓。
- 可以查看模拟净值曲线。
- 模拟盘可连续运行并记录每日状态。
- 模拟交易结果不影响真实资金。

