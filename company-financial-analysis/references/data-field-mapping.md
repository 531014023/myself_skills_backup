# API字段映射速查

> 从 westock-data 财报API输出到分析所需字段的映射关系

---

## 利润表 (lrb) — `finance sh600519 --type lrb`

| 分析字段 | API列名 | 单位转换 | 说明 |
|---------|---------|---------|------|
| 营业收入 | `OperatingRevenue` | ÷1e8 → 亿元 | 主营业务收入 |
| 营业总收入 | `TotalOperatingRevenue` | ÷1e8 | 含利息收入等 |
| 营业成本 | `OperatingCost` | ÷1e8 | |
| 销售费用 | `OperatingExpense` | ÷1e8 | ⚠️ 列名易误解，实际是销售费用 |
| 管理费用 | `TotalAdminExpense` | ÷1e8 | |
| 财务费用 | `FinancialExpense` | ÷1e8 | 负值=净利息收入 |
| 研发费用 | `RAndD` | ÷1e8 | |
| 营业利润 | `OperatingProfit` | ÷1e8 | |
| 利润总额 | `TotalProfit` | ÷1e8 | |
| 归母净利润 | `NPParentCompanyOwners` | ÷1e8 | ⚠️ 年报行是全年的，季报行是累计的 |
| 每股收益 | `BasicEPS` | 直接使用 | |

---

## 资产负债表 (zcfz) — `finance sh600519 --type zcfz`

| 分析字段 | API列名 | 索引 | 说明 |
|---------|---------|:--:|------|
| 总资产 | `TotalAssets` | - | |
| 流动资产合计 | `TotalCurrentAssets` | - | |
| 货币资金 | ⚠️ `CashEquivalents` | - | 这是现金及等价物，不是全部货币资金！ |
| 应收票据 | `BillAccReceivable` | - | |
| 其他应收款 | `OtherReceivableED` | - | |
| 预付账款 | `AdvancePayment` | - | |
| 预收款项 | `AdvanceReceipts` | - | 旧准则 |
| 合同负债 | `ContractLiability` | - | 新准则下的预收款项 |
| 存货 | `Inventories` | - | |
| 固定资产 | `TotalFixedAsset` | - | |
| 在建工程 | `TConstruInProcess` | - | |
| 无形资产 | `IntangibleAssets` | - | |
| 商誉 | ⚠️ 不在此API中 | - | 需单独查询 |
| 长期股权投资 | `LongtermEquityInvest` | - | |
| 交易性金融资产 | `TradingAssets` | - | |
| 投资性房地产 | `InvestmentProperty` | - | |
| 总负债 | `TotalLiability` | - | |
| 流动负债合计 | `TotalCurrentLiability` | - | |
| 有息负债 | `InterestBearDebt` | - | API计算值，含租赁负债+财务公司吸收存款 |
| 租赁负债 | `LeaseLiabilities` | - | |
| 一年内到期非流动负债 | `NonCurrentLiabilityIn1Year` | - | |
| 所有者权益合计 | `TotalShareholderEquity` | - | ⚠️ 净资产 |
| 资本公积 | `CapitalReserveFund` | - | |
| 盈余公积 | `SurplusReserveFund` | - | |
| 未分配利润 | `RetainedProfit` | - | |

---

## 现金流量表 (xjll) — `finance sh600519 --type xjll`

| 分析字段 | API列名 | 说明 |
|---------|---------|------|
| 经营现金流净额 | `NetOperateCashFlow` | |
| 销售收现 | `GoodsSaleServiceRenderCash` | 销售商品提供劳务收到的现金 |
| 投资现金流净额 | `NetInvestCashFlow` | |
| 筹资现金流净额 | `NetFinanceCashFlow` | ⚠️ 含借款和分红，不单独是分红 |
| 自由现金流(FCFE) | `FCFE` | 股权自由现金流 |
| 企业自由现金流(FCFF) | `FCFF` | |

---

## 需从 mx-data 单独获取的字段

这些字段 westock-data 的财报API不提供或不够精确：

| 字段 | mx-data查询示例 | 用途 |
|------|---------------|------|
| 资本开支 | `贵州茅台2016-2025年 购建固定资产无形资产和其他长期资产支付的现金` | OCF/FCF图(图19) |
| 分红付息 | `贵州茅台2016-2025年 分配股利利润或偿付利息支付的现金` | 现金综合图(图18) |
| 产品构成 | `贵州茅台主营收入构成 主营产品` | 产品堆叠柱状图(图3) |
| 地区构成 | `贵州茅台分地区收入` | 地区收入构成图(图4) |
| 渠道构成 | `贵州茅台分渠道收入 直销 经销 批发` | 渠道收入构成图(图4) |
| 客户集中度 | `贵州茅台前五大客户` | 公司基本信息 |
| 销售模式 | `贵州茅台直销 批发代理收入` | 渠道构成(图4) |
| 商誉 | `贵州茅台商誉` | 资产负债表（westock-data可能不含此字段） |

### v2.1 新增查询字段
| 字段 | mx-data查询示例 | 用途 |
|------|---------------|------|
| 流动比率 | `贵州茅台流动比率` | 安全性指标(图20) |
| 速动比率 | `贵州茅台速动比率` | 安全性指标(图20) |
| 应收账款周转率 | `贵州茅台应收账款周转率` | 营运能力(图23) |
| 存货周转率 | `贵州茅台存货周转率` | 营运能力(图23) |
| 固定资产周转率 | `贵州茅台固定资产周转率` | 营运能力(图23) |
| 总资产周转率 | `贵州茅台总资产周转率` | 杜邦分析(图5) |
| 资产负债率 | `贵州茅台资产负债率` | 杜邦分析(图5) |
| 负债明细 | `贵州茅台短期借款 长期借款 应付账款 合同负债` | 负债饼图(图7) |

---

## 港股字段映射（⚠️ 与A股完全不同）

### 综合损益表 (zhsy) — `finance hk00700 --type zhsy`

港股使用 `zhsy`（综合损益表）而非 `lrb`（利润表），字段名完全不同：

| 分析字段 | 港股API列名 | A股对应 | 说明 |
|---------|------------|---------|------|
| 营业收益/收入 | `OperatingIncome` | OperatingRevenue | |
| 毛利率 | `GrossIncomeRatio` | (计算) | 港股API直接给出% |
| 净利率 | `NetProfitRatio` | (计算) | 港股API直接给出% |
| 营业成本 | ⚠️ 需计算 | OperatingCost | `OperatingIncome × (1 - GrossIncomeRatio/100)` |
| 销售费用 | `SalesExpense` | OperatingExpense | |
| 管理费用 | `AdministrationExpense` | TotalAdminExpense | |
| 财务费用 | `FinancialCost` | FinancialExpense | |
| 营业利润 | `OperatingProfit` | OperatingProfit | |
| 税前利润 | `EarningBeforeTax` | TotalProfit | |
| 所得税 | `Tax` | (需计算) | |
| 归母净利润 | `ProfitToShareholders` | NPParentCompanyOwners | 母公司权益持有人应占溢利 |
| 少数股东损益 | `ProfitToMinority` | (需计算) | |
| 每股收益 | `BasicEPS` | BasicEPS | |
| ROE | `RoeWeighted` | (计算) | 加权ROE |
| ROA | `ROA` | (计算) | |
| 资产负债率 | `DebtAssetsRatio` | (计算) | |
| 经营费用(含研发) | `OperExpenses` | (含RAndD) | 港股经营费用=销售+管理+研发 |

### 资产负债表 (zcfz) — `finance hk00700 --type zcfz`

| 分析字段 | 港股API列名 | A股对应 | 说明 |
|---------|------------|---------|------|
| 总资产 | `TotalAssets` | TotalAssets | |
| 流动资产 | `TotalCurrentAssets` | TotalCurrentAssets | |
| 货币资金 | `Cash` | CashEquivalents | 港股直接叫Cash |
| 存货 | `Inventories` | Inventories | |
| 固定资产 | `FixedAssets` | TotalFixedAsset | |
| 在建工程 | `ConstruInProcess` | TConstruInProcess | |
| 无形资产 | `IntangibleAssets` | IntangibleAssets | |
| 投资性房地产 | `InvestmentProperty` | InvestmentProperty | |
| 长期借款 | `LongTermLoan` | (需计算) | |
| 应收账款 | `TotalAccountReceivable` | (分散) | 港股合计口径 |
| 应付账款 | `TotalAccountsPayable` | NotAccountsPayable | |
| 总负债 | `TotalLiability` | TotalLiability | |
| 流动负债 | `TotalCurrentLiability` | TotalCurrentLiability | |
| 净资产(含少数) | `TotalEquity` | TotalShareholderEquity | |
| 归母权益 | `SeWithoutMinority` | (计算) | Shareholder Equity w/o Minority |
| 递延所得税资产 | `DeferTaxAssets` | (需查A股) | |
| 递延所得税负债 | `DeferTaxLiability` | (需查A股) | |

### 现金流量表 (xjll) — `finance hk00700 --type xjll`

| 分析字段 | 港股API列名 | A股对应 | 说明 |
|---------|------------|---------|------|
| 经营现金流 | `CFO` | NetOperateCashFlow | Cash Flow from Operations |
| 投资现金流 | `CFI` | NetInvestCashFlow | |
| 筹资现金流 | `CFF` | NetFinanceCashFlow | |
| 销售收现 | `CashReceiptsfope` | GoodsSaleServiceRenderCash | |
| 资本开支 | `Purcapitalassents` | (mx-data获取) | Purchase of capital assets |
| 分红付息 | `Dividendinterestpayment` | (mx-data获取) | |
| 发行债券 | `Cashfrbondsiss` | (无需) | |
| 借款流入 | `Cashfrborrowing` | (无需) | |
| 偿还借款 | `Borrowingrepayment` | (无需) | |
| 期初现金 | `BeginPeriodCash` | (无需) | |
| 期末现金 | `Endperiodce` | (无需) | |

### 港股特有指标（可直接使用）

港股API直接提供了很多A股需要计算的比率：
- `GrossIncomeRatio` — 毛利率(%)
- `NetProfitRatio` — 净利率(%)
- `OperatingProfitRatio` — 营业利润率(%)
- `RoeWeighted` — 加权ROE(%)
- `ROA` — 总资产收益率(%)
- `DebtAssetsRatio` — 资产负债率(%)
- `CurrentRatio` — 流动比率
- `QuickRatio` — 速动比率
- `BasicEpsGr1y` — EPS同比增长率
- `NetProfitGr1y` — 净利同比增长率

### 货币单位

⚠️ 港股返回港元/美元，**必须标注正确货币单位，禁止使用人民币符号¥**

在报告中将"亿元"改为"亿港元"或"亿港元(约X亿人民币)"。


