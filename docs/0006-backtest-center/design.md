# Backtest Center 回测中心详细设计

## 1. 模块目标

回测中心负责在历史数据上模拟策略运行，验证策略是否有效。它是 QuantDash 从“看板”走向“量化系统”的核心模块。

## 2. 模块边界

### 2.1 模块内职责

- 管理回测任务。
- 加载历史数据、股票池、因子和策略版本。
- 执行日频事件驱动回测。
- 模拟手续费、滑点、T+1、停牌、涨跌停。
- 输出收益曲线、回撤曲线、交易明细、持仓明细和风险指标。

### 2.2 模块外职责

- 不负责原始数据清洗。
- 不负责策略定义。
- 不负责实盘下单。
- 不负责人工投资建议。

## 3. 技术架构

```text
Backtest Config
  -> Data Snapshot Loader
  -> Strategy Signal Runner
  -> Portfolio Builder
  -> Risk/Execution Simulator
  -> Account Ledger
  -> Report Generator
```

第一版建议只做 A 股日频回测，不做分钟级和高频。

## 4. 数据模型

```ts
type BacktestConfig = {
  strategy_id: string;
  strategy_version: string;
  universe_id: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
  benchmark: string;
  commission_rate: number;
  slippage_rate: number;
  rebalance_frequency: "daily" | "weekly" | "monthly";
  max_positions: number;
  max_weight_per_symbol: number;
};
```

```ts
type BacktestMetrics = {
  annual_return: number;
  max_drawdown: number;
  sharpe: number;
  calmar: number;
  win_rate: number;
  turnover: number;
  excess_return: number;
};
```

## 5. 回测流程

```text
创建回测任务
  -> 锁定数据版本、股票池版本、策略版本
  -> 从 start_date 逐日推进
  -> 每个交易日加载当日可见数据
  -> 策略生成信号
  -> 组合模块生成目标仓位
  -> 风控模块检查
  -> 执行模拟成交
  -> 更新现金、持仓、净值
  -> 生成指标和报告
```

## 6. 交易约束

- T+1：当天买入的股票当天不能卖出。
- 停牌：停牌股票不可买卖。
- 涨停：涨停股票不可买入。
- 跌停：跌停股票不可卖出。
- 流动性：单笔成交金额不得超过当日成交额的设定比例。
- 手续费和滑点必须从成交结果中扣除。

## 7. API 设计

```text
POST /api/backtests
GET /api/backtests
GET /api/backtests/[id]
GET /api/backtests/[id]/equity-curve
GET /api/backtests/[id]/drawdown
GET /api/backtests/[id]/positions
GET /api/backtests/[id]/trades
GET /api/backtests/[id]/logs
```

## 8. 独立测试设计

- 使用 3 只股票、10 个交易日的小样本做确定性回测。
- 单独测试手续费、滑点、T+1、涨跌停、停牌规则。
- 测试同一配置重复运行结果一致。
- 测试策略不能读取未来日期数据。
- 测试回测指标计算正确。

## 9. 验收标准

- 可以跑完一个 3 年日频回测。
- 可以展示收益、回撤、交易明细、每日持仓。
- 回测结果可复现。
- 回测不允许未来函数和幸存者偏差。

