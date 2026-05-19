# 0001 Define Factor Models And Store

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0004-factor-engine/design.md`

## 目标

定义因子元数据、因子值和因子版本存储，让策略和回测可以按日期读取可复现因子快照。

## 前置依赖

- `data-center` 已提供清洗后的行情、财务和舆情数据。
- `universe-center` 已提供股票池快照。
- 待确认因子存储使用 PostgreSQL 还是 Parquet/DuckDB。

## 执行步骤

1. 定义 `FactorDefinition`，包含名称、展示名、类别、版本、频率、输入和描述。
2. 定义 `FactorValue`，包含日期、股票、因子名、版本和值。
3. 设计因子版本规则，因子逻辑或参数变化必须生成新版本。
4. 设计因子存储访问层，先隐藏 PostgreSQL 与 Parquet/DuckDB 的具体实现差异。
5. 对缺失值使用 `null` 或明确填充策略，不默认填 0。
6. 为因子读取接口设计按日期、股票池、因子名和版本查询能力。

## 产出

- 因子定义模型。
- 因子值存储模型。
- 因子版本规则。
- 因子读取访问层。

## 验收

- 可以保存并查询历史因子值。
- 同一因子不同版本可并存。
- 策略和回测可以按日期读取因子快照。

