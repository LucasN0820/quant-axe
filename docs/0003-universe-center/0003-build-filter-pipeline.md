# 0003 Build Filter Pipeline

来源：`docs/proposal.md`、`docs/total_progress.md`、`docs/0003-universe-center/design.md`

## 目标

实现管道式过滤器，支持 ST、停牌、上市天数、流动性、价格和涨跌停交易状态处理。

## 前置依赖

- `data-center` 已提供 ST、停牌、涨跌停、成交额和上市日期数据。
- 基础股票池 provider 已完成。

## 执行步骤

1. 定义过滤器统一接口：输入日期和候选股票，输出纳入状态和原因。
2. 实现 `STFilter`，剔除 ST 股票。
3. 实现 `SuspensionFilter`，剔除停牌股票。
4. 实现 `ListedDaysFilter`，剔除上市不足 N 天股票。
5. 实现 `LiquidityFilter`，剔除成交额不足股票。
6. 实现 `PriceFilter`，剔除价格过低或过高股票。
7. 实现 `LimitUpDownFilter`，标记涨停不可买和跌停不可卖。
8. 保留每个过滤器的剔除原因，避免原因被后续过滤器覆盖。

## 产出

- 可组合过滤器管道。
- 各过滤器单独配置和执行能力。
- 剔除原因记录。

## 验收

- 可以创建“沪深 300 + 剔除 ST + 剔除停牌”的股票池。
- 被剔除股票有明确原因。
- 每个过滤器可单独测试。

