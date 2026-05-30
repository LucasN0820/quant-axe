# 0006 TuShare → AkShare 迁移字段缺口

来源：TuShare 高积分接口（`daily_basic` / `fina_indicator` / `index_weight` / `anns`）迁移至 AkShare 后的字段差异记录。

## 背景

当前 TuShare 积分不足以支撑 `daily_basic`(2000)、`fina_indicator`(2000)、`index_weight`(2000) 和 `anns`(独立权限 1000 元/年) 四个接口。已将其迁移至 AkShare 等价接口，`stock_basic`(120 免费积分) 仍然保留在 TuShare。

---

## 1. daily_basic → stock_zh_a_spot_em()

| 缺失字段 | 中文含义 | 说明 |
|----------|----------|------|
| `pe` | 静态市盈率 | 基于上年度净利润的市盈率。AkShare 现货表仅提供 `市盈率-动态`（即 PE TTM），无静态 PE。 |
| `ps_ttm` | 滚动市销率 | 总市值 ÷ 近 12 个月营业收入，用于衡量收入创造市值的能力。东方财富现货接口不提供此字段。 |
| `dv_ttm` | 滚动股息率 | 近 12 个月每股股利 ÷ 当前股价，反映分红回报率。需从 `stock_dividents_em` 单独获取股利数据后自行计算。 |
| `turnover_rate_f` | 自由流通换手率 | 基于自由流通股本的换手率，区别于总股本口径的换手率。东方财富仅提供总股本口径换手率。 |
| `total_share` | 总股本（万股） | 上市公司发行在外的全部股数。东方财富现货表不提供，需从 `stock_individual_info_em` 单独获取。 |
| `float_share` | 自由流通股本（万股） | 扣除大股东、董监高等限售部分的实际可交易股数。东方财富现货表不提供。 |

**替代后的 AkShare 接口**：`ak.stock_zh_a_spot_em()`，来源为东方财富实时行情快照。该接口一次性返回全市场约 5000 只 A 股的实时数据，按代码过滤即可得到单只标的。

**可获取的字段**：`close`（最新价）、`pe_ttm`（市盈率-动态）、`pb`（市净率）、`turnover_rate`（换手率%）、`total_mv`（总市值）、`circ_mv`（流通市值）。

---

## 2. fina_indicator → stock_financial_analysis_indicator_em()

| 缺失字段 | 中文含义 | 说明 |
|----------|----------|------|
| `roe_dt` | 稀释净资产收益率 | 考虑可转债、期权、限制性股票等潜在稀释因素调整后的 ROE。东方财富财务分析接口不提供此口径。 |

**替代后的 AkShare 接口**：`ak.stock_financial_analysis_indicator_em(symbol, indicator="按报告期")`，来源为东方财富数据中心-财务分析指标。

**可获取的字段**：`report_period`（报告期）、`roe`（净资产收益率%）、`roe_waa`（加权净资产收益率%）、`gross_margin`（销售毛利率%）、`netprofit_margin`（销售净利率%）、`debt_to_assets`（资产负债率%）、`revenue_yoy`（主营业务收入增长率%）、`netprofit_yoy`（净利润增长率%）、`assets_yoy`（总资产增长率%）。

---

## 3. index_weight → index_stock_cons_weight_csindex()

无字段缺失。权重数据来自中证指数官网，返回日期、成分券代码/名称、权重（%），与原 TuShare `index_weight` 接口字段一一对应。

**差异**：仅返回最新交易日数据（无历史快照）。当前代码本就只取最新 `trade_date` 对应记录，无实际影响。

**替代后的 AkShare 接口**：`ak.index_stock_cons_weight_csindex(symbol="000300")`，来源为中证指数有限公司官网。

---

## 4. anns → stock_notice_report()

无字段缺失。返回公告标题、公告链接、公告日期，与原 TuShare `anns` 接口字段一一对应。

**差异**：AkShare 接口按单日查询（`date="20250530"`），不支持一次返回多日公告。当前实现通过逐日回查最近交易日来累积至所需的 `limit` 条数（最多回查 90 个自然日）。

**替代后的 AkShare 接口**：`ak.stock_notice_report(symbol, date)`，来源为东方财富-数据中心-公告。

---

## 5. 前端影响评估

前端 `FinancialSummaryPanel` 渲染的 6 个指标及其数据来源：

| 展示指标 | 原 TuShare 来源 | 现 AkShare 来源 | 是否受影响 |
|----------|----------------|----------------|-----------|
| PE TTM | `daily_basic.pe_ttm` | `stock_zh_a_spot_em` 市盈率-动态 | 否 |
| PB | `daily_basic.pb` | `stock_zh_a_spot_em` 市净率 | 否 |
| ROE | `fina_indicator.roe` | `stock_financial_analysis_indicator_em` 净资产收益率(%) | 否 |
| 毛利率 | `fina_indicator.gross_margin` | `stock_financial_analysis_indicator_em` 销售毛利率(%) | 否 |
| 营收同比 | `fina_indicator.revenue_yoy` | `stock_financial_analysis_indicator_em` 主营业务收入增长率(%) | 否 |
| 净利同比 | `fina_indicator.netprofit_yoy` | `stock_financial_analysis_indicator_em` 净利润增长率(%) | 否 |

**以上 6 个字段均未受影响，前端无需改动。**

---

## 6. 数据库影响

`financial_metrics` 表及 `raw_payloads` 表中以下列在迁移后将存为 `NULL`：

- `pe`（静态市盈率）
- `ps_ttm`（滚动市销率）
- `dv_ttm`（滚动股息率）
- `total_share`（总股本）
- `float_share`（自由流通股本）
- `turnover_rate_f`（自由流通换手率）
- `roe_dt`（稀释 ROE）

后续若有需求（如回测模块需要静态 PE 或 PS TTM），可考虑从 `stock_individual_info_em`（总股本）、`stock_dividents_em`（股利）等 AkShare 接口补充数据并自行计算。

---

## 7. 存量 TuShare 接口

唯一保留的 TuShare 接口为 `stock_basic`（120 免费积分），用于补充股票基础信息（名称、行业、上市日期）。若后续注册积分用完或接口不可用，可降级至 AkShare `stock_info_a_code_name`（仅代码+名称，无行业和上市日期）。
