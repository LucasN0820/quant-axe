# 0004 Factor Analysis And Extended Factors

来源：`docs/0004-factor-engine/design.md`、`docs/0004-factor-engine/progress.md`

## 目标

补齐因子分析接口，并实现价值、质量和舆情等扩展因子。

## 前置依赖

- P0 基础因子已完成。
- 财务和舆情数据可用。

## 执行步骤

1. 实现 PE/PB 价值因子。
2. 实现 ROE/毛利率质量因子。
3. 实现舆情热度因子。
4. 实现因子覆盖率统计。
5. 实现因子分布统计。
6. 实现分组收益。
7. 实现 IC 和 Rank IC。
8. 实现 `GET /api/factors/[name]/analysis`。
9. 使用小样本验证分组收益和 IC 计算。

## 产出

- P1/P2 扩展因子。
- 因子分析接口。
- 因子分析测试。

## 验收

- 可以查看因子覆盖率和分布。
- 可以评估单因子的分组收益和 IC。
- 财务因子不使用未披露的未来财报。

