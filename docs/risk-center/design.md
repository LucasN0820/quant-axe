# Risk Center 风控中心详细设计

## 1. 模块目标

风控中心负责在策略、组合、回测、模拟交易和实盘交易前检查风险，防止异常数据、异常仓位或异常订单造成不可接受损失。

## 2. 模块边界

### 2.1 模块内职责

- 维护风控规则。
- 检查订单是否允许执行。
- 检查组合是否超过风险限制。
- 对异常数据、停牌、涨跌停、流动性不足进行拦截。
- 输出阻塞原因和警告。

### 2.2 模块外职责

- 不生成策略信号。
- 不计算目标仓位。
- 不执行真实订单。
- 不替代用户投资判断。

## 3. 技术架构

```text
Order / Portfolio Snapshot
  -> Risk Rule Engine
  -> Data Center Trading State
  -> Pass / Block / Warning
```

规则设计为可组合的独立检查器：

```text
PositionLimitRule
IndustryLimitRule
LiquidityRule
SuspensionRule
LimitUpDownRule
DrawdownRule
DataQualityRule
```

## 4. 数据模型

```ts
type RiskLimit = {
  max_weight_per_symbol: number;
  max_weight_per_industry: number;
  max_total_exposure: number;
  max_daily_loss?: number;
  max_drawdown?: number;
  max_order_value?: number;
};
```

```ts
type RiskCheckResult = {
  passed: boolean;
  blocked_reasons: string[];
  warnings: string[];
};
```

## 5. 风控规则

| 规则 | 行为 |
| --- | --- |
| 单票仓位 | 超过上限则阻塞 |
| 行业仓位 | 超过行业上限则阻塞或警告 |
| 总仓位 | 超过总暴露则阻塞 |
| 流动性 | 订单金额超过成交额比例则阻塞 |
| 停牌 | 停牌股票不可交易 |
| 涨停 | 涨停不可买入 |
| 跌停 | 跌停不可卖出 |
| 数据异常 | 缺失关键价格时阻塞 |
| 回撤 | 超过阈值暂停策略或降仓 |

## 6. API 设计

```text
POST /api/risk/check-order
POST /api/risk/check-portfolio
GET /api/risk/limits
PATCH /api/risk/limits
GET /api/risk/events
```

## 7. 独立测试设计

- 构造超过单票上限的订单，验证被阻塞。
- 构造停牌股票订单，验证被阻塞。
- 构造涨停买入和跌停卖出，验证被阻塞。
- 构造数据缺失行情，验证被阻塞。
- 组合总仓位超限时输出明确原因。

## 8. 验收标准

- 所有交易前都能调用风控检查。
- 风控结果包含清晰阻塞原因。
- 回测、模拟交易和实盘交易复用同一套规则。
- 风控规则可单独测试，不依赖 UI。

