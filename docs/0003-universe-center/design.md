# Universe Center 股票池中心详细设计

## 1. 模块目标

股票池中心负责定义“策略在某个历史日期允许交易哪些股票”。它为因子计算、策略研究和回测提供可复现的股票范围，避免新手直接对全市场无约束运行策略。

## 2. 模块边界

### 2.1 模块内职责

- 管理内置股票池和自定义股票池。
- 配置过滤条件。
- 按日期生成股票池成分。
- 记录剔除原因。
- 为回测提供历史可复现的股票池快照。

### 2.2 模块外职责

- 股票基础数据、ST、停牌、指数成分由 `data-center` 提供。
- 因子排名由 `factor-engine` 提供。
- 策略买卖规则由 `research-lab` 提供。

## 3. 技术架构

```text
Universe Config
  -> Data Center snapshots
  -> Filter Pipeline
  -> Universe Snapshot
  -> API / Backtest Reader
```

过滤器采用管道式设计，每个过滤器只处理一个条件：

```text
BaseUniverseProvider
  -> STFilter
  -> SuspensionFilter
  -> ListedDaysFilter
  -> LiquidityFilter
  -> PriceFilter
  -> LimitUpDownFilter
```

## 4. 数据模型

```ts
type Universe = {
  id: string;
  name: string;
  base: "all_a" | "hs300" | "zz500" | "zz1000" | "custom";
  filters: UniverseFilter[];
  created_at: string;
  updated_at: string;
};
```

```ts
type UniverseMember = {
  date: string;
  universe_id: string;
  symbol: string;
  name: string;
  included: boolean;
  excluded_reason?: string;
};
```

## 5. API 设计

```text
GET /api/universes
POST /api/universes
GET /api/universes/[id]
PATCH /api/universes/[id]
DELETE /api/universes/[id]
GET /api/universes/[id]/stocks?date=YYYY-MM-DD
POST /api/universes/[id]/preview
POST /api/universes/[id]/snapshot
```

## 6. 过滤规则

| 过滤器 | 输入 | 输出 |
| --- | --- | --- |
| STFilter | `stock_status` | 剔除 ST 股票 |
| SuspensionFilter | `stock_status` | 剔除停牌股票 |
| ListedDaysFilter | `stock_profiles` + date | 剔除上市不足 N 天股票 |
| LiquidityFilter | `daily_bars` | 剔除成交额不足股票 |
| PriceFilter | `daily_bars` | 剔除价格过低/过高股票 |
| LimitUpDownFilter | `limit_prices` | 标记涨停不可买、跌停不可卖 |

## 7. 独立测试设计

- 每个过滤器使用小样本输入单独测试。
- 同一日期、同一配置生成结果必须稳定。
- 回测读取历史股票池时，不允许使用未来日期的数据。
- 剔除原因必须可解释，便于用户学习和排查。

## 8. 验收标准

- 可以创建“沪深 300 + 剔除 ST + 剔除停牌”的股票池。
- 可以查看任意交易日的股票池成分。
- 可以看到每只被剔除股票的原因。
- 回测能按历史日期读取对应股票池快照。

