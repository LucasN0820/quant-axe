# Research Lab 策略研究详细设计

## 1. 模块目标

策略研究模块负责把投资想法转化为明确、可执行、可回测的策略规则。它不直接下单，也不直接计算历史收益，而是生成信号或目标持仓，交给回测、组合和风控模块处理。

## 2. 模块边界

### 2.1 模块内职责

- 管理策略定义和策略版本。
- 管理策略参数。
- 调用股票池和因子数据生成信号。
- 提供新手友好的策略模板。
- 输出可解释的买入、卖出、持有理由。

### 2.2 模块外职责

- 数据由 `data-center` 提供。
- 股票范围由 `universe-center` 提供。
- 因子值由 `factor-engine` 提供。
- 收益验证由 `backtest-center` 负责。
- 仓位权重由 `portfolio-center` 负责。
- 风控拦截由 `risk-center` 负责。

## 3. 技术架构

```text
Strategy Template / Python Strategy
  -> Strategy Params
  -> Context Loader
  -> Signal Generator
  -> Signal Store
  -> Backtest / Paper Trading
```

策略实现建议使用 Python 插件式结构：

```text
backend/app/strategies/
  momentum_v1.py
  value_quality_v1.py
  sentiment_event_v1.py
```

每个策略暴露统一入口：

```python
def generate_signals(context) -> list[Signal]:
    ...
```

## 4. 数据模型

```ts
type StrategyDefinition = {
  id: string;
  name: string;
  version: string;
  template: "momentum" | "value_quality" | "sentiment_event" | "custom";
  universe_id: string;
  params: Record<string, unknown>;
  created_at: string;
};
```

```ts
type Signal = {
  date: string;
  strategy_id: string;
  strategy_version: string;
  symbol: string;
  action: "buy" | "sell" | "hold";
  score?: number;
  reason: string;
};
```

## 5. 新手策略模板

### 5.1 动量策略

```text
股票池：沪深 300 / 中证 500
因子：20 日涨幅
过滤：ST、停牌、成交额不足、涨跌停
买入：排名前 N
卖出：跌出排名阈值或调仓日不在目标列表
持仓：交给组合模块等权
```

### 5.2 价值质量策略

```text
股票池：全 A 或沪深 300
因子：低 PB、高 ROE
过滤：财务异常、流动性不足
买入：综合分数排名前 N
```

### 5.3 情绪事件策略

```text
候选：舆情热度上升且新闻数量增加
过滤：连续大涨、流动性不足
风控：持有天数和单票仓位严格限制
```

## 6. API 设计

```text
GET /api/strategies
POST /api/strategies
GET /api/strategies/[id]
PATCH /api/strategies/[id]
POST /api/strategies/[id]/preview-signals
GET /api/strategies/[id]/signals?date=YYYY-MM-DD
```

## 7. 独立测试设计

- 使用固定股票池和固定因子值测试策略输出。
- 策略生成信号时不得读取未来日期数据。
- 参数变更后生成新的策略版本。
- 对同一输入，策略输出必须确定。
- 策略 preview 不依赖回测引擎即可运行。

## 8. 验收标准

- 用户可以配置一个 20 日动量策略。
- 策略能在指定日期输出买入/卖出信号。
- 每条信号包含理由，便于新手理解。
- 回测可以绑定策略版本和参数。

