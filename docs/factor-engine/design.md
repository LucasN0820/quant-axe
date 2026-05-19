# Factor Engine 因子引擎详细设计

## 1. 模块目标

因子引擎负责把行情、财务、新闻、舆情等数据转化为可用于策略研究和回测的量化指标。对新手来说，因子就是“给股票打分的规则”。

## 2. 模块边界

### 2.1 模块内职责

- 定义因子元数据。
- 计算单因子或批量因子。
- 保存因子值和因子版本。
- 提供因子分析结果。
- 为策略和回测提供历史因子读取能力。

### 2.2 模块外职责

- 原始数据由 `data-center` 提供。
- 股票范围由 `universe-center` 提供。
- 策略如何使用因子由 `research-lab` 决定。
- 组合权重由 `portfolio-center` 决定。

## 3. 技术架构

```text
Factor Definition
  -> Data Loader
  -> Factor Calculator
  -> Factor Store
  -> Factor Analysis
  -> Strategy/Backtest API
```

因子计算建议在 Python 后端实现，前端只负责配置、触发、查看结果。

## 4. 因子分类

| 类型 | 示例 | 优先级 |
| --- | --- | --- |
| 动量 | 20 日涨幅、60 日涨幅 | P0 |
| 反转 | 1 日跌幅、5 日跌幅 | P0 |
| 流动性 | 成交额均值、换手率 | P0 |
| 波动 | 20 日波动率、最大回撤 | P1 |
| 价值 | PE TTM、PB | P1 |
| 质量 | ROE、毛利率 | P1 |
| 成长 | 营收增长、利润增长 | P2 |
| 情绪 | 热度、新闻数量、热度变化 | P2 |

## 5. 数据模型

```ts
type FactorDefinition = {
  name: string;
  display_name: string;
  category: string;
  version: string;
  frequency: "daily" | "weekly" | "monthly";
  inputs: string[];
  description: string;
};
```

```ts
type FactorValue = {
  date: string;
  symbol: string;
  factor_name: string;
  factor_version: string;
  value: number | null;
};
```

## 6. API 设计

```text
GET /api/factors
GET /api/factors/[name]
POST /api/factors/run
GET /api/factors/[name]/values?date=YYYY-MM-DD&universe_id=
GET /api/factors/[name]/analysis?start=&end=&universe_id=
```

## 7. 计算规则

- 因子必须只使用当前日期及以前可获得的数据。
- 财务因子必须考虑财报披露日期，不能使用未来财报。
- 因子计算结果必须记录版本。
- 缺失值不随意填 0，需要记录为 `null` 或使用明确填充策略。

## 8. 因子分析

第一阶段支持：

- 覆盖率。
- 分布统计。
- 分组收益。
- IC。
- Rank IC。

## 9. 独立测试设计

- 使用固定行情样本测试 20 日动量。
- 使用固定成交额样本测试流动性因子。
- 使用缺失值样本测试空值处理。
- 使用不同日期测试是否出现未来函数。
- 因子分析使用小样本验证分组收益和 IC 计算。

## 10. 验收标准

- 可以计算某日某股票池的 20 日动量。
- 可以保存并查询历史因子值。
- 可以查看因子覆盖率和分布。
- 策略和回测可以按日期读取因子快照。

