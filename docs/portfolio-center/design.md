# Portfolio Center 组合中心详细设计

## 1. 模块目标

组合中心负责把策略信号转换为目标持仓和调仓计划。策略告诉系统“买哪些股票”，组合中心决定“每只买多少”。

## 2. 模块边界

### 2.1 模块内职责

- 根据策略信号生成目标权重。
- 应用组合层约束。
- 从当前持仓和目标持仓生成调仓计划。
- 提供等权、因子分数加权、波动率倒数加权等组合方法。

### 2.2 模块外职责

- 不负责生成策略信号。
- 不负责校验停牌、涨跌停等交易级风控。
- 不负责模拟成交或实盘下单。

## 3. 技术架构

```text
Signals
  -> Weighting Model
  -> Portfolio Constraints
  -> Target Positions
  -> Rebalance Plan
```

新手阶段优先实现等权组合，降低理解和调试成本。

## 4. 数据模型

```ts
type TargetPosition = {
  portfolio_id: string;
  date: string;
  symbol: string;
  target_weight: number;
  target_value?: number;
};
```

```ts
type RebalanceOrderPlan = {
  symbol: string;
  side: "buy" | "sell";
  target_weight: number;
  current_weight: number;
  delta_weight: number;
  estimated_value: number;
};
```

## 5. 组合方法

| 方法 | 说明 | 优先级 |
| --- | --- | --- |
| 等权 | 每只股票权重相同 | P0 |
| 因子分数加权 | 分数越高权重越大 | P1 |
| 波动率倒数加权 | 波动越低权重越高 | P1 |
| 行业中性 | 控制行业暴露 | P2 |

## 6. 约束规则

- 单票最大仓位。
- 行业最大仓位。
- 总仓位上限。
- 现金保留比例。
- 最大持仓数量。
- 最小交易金额，避免碎片订单。

## 7. API 设计

```text
POST /api/portfolios/target
GET /api/portfolios/[id]/positions
GET /api/portfolios/[id]/target-positions
GET /api/portfolios/[id]/rebalance-plan
```

## 8. 独立测试设计

- 给定 10 个买入信号，等权组合应每只 10%。
- 设置单票上限后，目标权重不得超过上限。
- 当前持仓和目标持仓差异应生成正确买卖方向。
- 现金保留比例生效。
- 空信号时返回空目标仓位。

## 9. 验收标准

- 策略信号可以生成目标持仓。
- 目标持仓可以生成调仓计划。
- 单票、行业、总仓位约束能够生效。
- 回测和模拟交易都能复用组合输出。

