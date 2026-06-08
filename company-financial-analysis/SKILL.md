---
name: company-financial-analysis
description: 企业财务深度分析工具。基于唐朝《手把手教你读财报2021》方法论，对上市公司进行五轮递进式财务分析。从鸟瞰概览到结构拆解，再到四步排雷分析，最后输出交互式HTML报告。适用于A股、港股、美股。
version: 2.2.0
author: 银月
created: 2026-06-04
updated: 2026-06-05
agent_created: true
triggers:
  - "分析XXX"
  - "企业分析"
  - "财务分析"
  - "XXX公司深度分析"
  - "帮我看看XXX"
  - "财报分析XXX"
  - "分析一下XXX的财务"
  - "研究一下XXX公司"
data_sources:
  - westock-data (三表主数据，优先)
  - mx-data (资本开支/分红子项/产品地区构成)
  - neodata-financial-search (补充久远年度数据)
dependencies:
  - westock-data
  - mx-data
  - neodata-financial-search
output: HTML报告 → 公司研究/{公司名称}/{公司名称}_企业分析_{日期}.html
---

# 企业财务深度分析 Skill v2.3

基于唐朝《手把手教你读财报2021(新准则升级版)》方法论的上市公司财务分析工具。

> **v2.3 核心变更**（2026-06-06）：
> - 费用率改为堆叠柱状图（销售+管理+研发=综合费用率）+ 毛利率右轴折线
> - 杜邦拆解：净利率/周转率/乘数改为并排柱状图，移除资产负债率/费用率
> - 资产负债饼图：按具体会计科目展示，不按计算分组
> - 自由现金流堆叠图：每根柱子=FCF(bottom)+Capex(top)=OCF
> - ECharts CDN：cdnjs.cloudflare.com
> - 数据处理：pd.to_numeric 必须用 errors='coerce'
>
> **v2.2 核心变更**（2026-06-05）：
> - 营收和归母净利润拆分为独立图表（每张柱状图显示金额 + 折线图显示同比增长率）
> - 移除三表全科目数据表（数据仅供图表使用，不单独展示）
> - 杜邦拆解合并为单图（7系列同一grid）
> - 新增负债结构饼图、产品堆叠柱状图、地区/渠道构成图
> - 成长性图表图例颜色显式指定
> - 所有数据至少10年（上市不满10年取全部）

## 激活条件

当用户输入以下意图时触发：
- 股票代码（如 600519、09992.HK、AAPL）
- 公司名称 + "分析" / "研究" / "帮我看看"
- 明确的"财报分析""财务分析"请求

---

## 🔴 核心原则（必须严格遵守）

### 数据原则

1. **数据必须从API直接获取，禁止硬编码、禁止估算、禁止凑数据**
   - 三张表主数据 → `westock-data finance --num 40`（40期可覆盖约10年年报）
   - 资本开支（购建固定资产支付的现金）→ `mx-data`
   - 分红（分配股利利润或偿付利息支付的现金）→ `mx-data`
   - 产品/地区/销售构成 → `mx-data`
   - 股价K线 → `westock-data kline --period year`

2. **数据覆盖范围必须标注清楚**
   - 财报数据受API追溯限制，通常覆盖近10年（如2016-2025）
   - 股价数据通常可追溯到IPO（如2001-2025）
   - 在报告顶部用蓝色信息框明确标注各数据来源和覆盖年份
   - 如果API只有3年数据就说3年，不要为了"完整"去估算

3. **禁止行为**
   - ❌ 不读API直接凭记忆填数据
   - ❌ API只返回3年却硬凑10年或25年
   - ❌ 用 `ocf * 1.15` 之类系数估算缺失数据
   - ❌ 在图表标题写"估"字——宁可缺数据也不要估算
   - ❌ 用错误的列索引提取数据（如把长期借款当成净资产）
   - ❌ **用 `pd.to_numeric(x)` 而不是 `pd.to_numeric(x, errors='coerce')`**——早期年份含'-'的字段（如RAndD）会导致整列保持字符串，后续计算严重错误

### 分析原则

4. **每个图表必须配深度分析文字**（200-400字），不能只放图
5. **分析要有数据支撑**，引用具体数字和变化幅度
6. **异常先查附注原因，找不到就标注疑点**
7. **财报是用来排除企业的** — 怀疑优先于信任

---

## 数据获取规范

### 🔴 数据年限要求（v2.1）

**所有时间序列数据至少覆盖10年**（上市不满10年取全部）。在报告头部用蓝色信息框明确标注数据覆盖年份。

### 第一步：获取三表主数据
```bash
# 获取最近40期财务数据（约10年年报+季报）
# 资产负债表、利润表、现金流量表所有科目全部获取
node westock-data/scripts/index.js finance sh600519 --num 40 > raw.txt
```

### 第二步：解析并提取年报数据
从 raw.txt 中解析 markdown 表格，筛选 `12-31` 行即为年报数据。
- 提取**资产负债表所有科目**、**利润表所有科目**、**现金流量表所有科目**
- 至少保留10年年报数据（上市不满10年取全部）

### 第三步：获取子项数据（mx-data）
```bash
# 资本开支 + 分红（mx-data可返回更细粒度）
cd mx-data && python mx_data.py "贵州茅台2016-2025年 购建固定资产支付的现金 分配股利支付的现金"

# 产品/地区/渠道构成
cd mx-data && python mx_data.py "贵州茅台主营收入构成 分地区收入 分渠道收入 前五大客户"

# 财务指标补充（如果westock-data不完整）
cd mx-data && python mx_data.py "贵州茅台ROE 毛利率 净利率 资产负债率 流动比率 速动比率"
```

### 第四步：获取股价
```bash
westock-data kline sh600519 --period year --limit 30 --fq bfq
```

### 第五步：计算衍生指标（v2.1新增）
从三表数据中计算以下指标（10年数据）：
- **费用率**：销售费用率、管理费用率、财务费用率、综合费用率
- **周转率**：应收账款周转率、存货周转率、固定资产周转率、总资产周转率
- **安全性**：流动比率、速动比率、资产负债率、现金债务比
- **成长性**：营收增长率、归母净利润增长率、总资产增长率、净资产增长率
- **杜邦分解**：ROE、净利率、总资产周转率、权益乘数

计算公式详见 `chart-specs.md` → 计算指标速查。

---

## 关键字段映射

### A股（lrb/zcfz/xjll）：详见 `references/data-field-mapping.md`

### 港股（zhsy/zcfz/xjll）：⚠️ 字段名与A股完全不同！

| 分析需要 | A股字段 | 港股字段 | 
|---------|---------|---------|
| 营业收入 | OperatingRevenue | **OperatingIncome** |
| 毛利率 | (rev-cost)/rev | **GrossIncomeRatio**（直接给出%） |
| 销售费用 | OperatingExpense | **SalesExpense** |
| 管理费用 | TotalAdminExpense | **AdministrationExpense** |
| 财务费用 | FinancialExpense | **FinancialCost** |
| 归母净利润 | NPParentCompanyOwners | **ProfitToShareholders** |
| 货币资金 | CashEquivalents | **Cash** |
| 净资产 | TotalShareholderEquity | **TotalEquity** |
| 归母权益 | (计算) | **SeWithoutMinority** |
| 经营现金流 | NetOperateCashFlow | **CFO** |
| 投资现金流 | NetInvestCashFlow | **CFI** |
| 筹资现金流 | NetFinanceCashFlow | **CFF** |
| 资本开支 | (mx-data获取) | **Purcapitalassents** |
| 分红 | (mx-data获取) | **Dividendinterestpayment** |

**港股查询命令差异**：`finance hk00700 --type zhsy`（不是lrb）

**货币单位**：港股返回港元，报告中必须标注"亿港元"，禁止使用¥符号。

完整映射见 `references/data-field-mapping.md` → 港股字段映射。

---

### A股关键字段速查

| 分析需要 | API字段 | 换算 |
|---------|---------|------|
| 营业收入 | `OperatingRevenue` | ÷1e8 = 亿元 |
| 营业成本 | `OperatingCost` | ÷1e8 |
| 销售费用 | `OperatingExpense` | ÷1e8 |
| 管理费用 | `TotalAdminExpense` | ÷1e8 |
| 财务费用 | `FinancialExpense` | ÷1e8（负=净收入） |
| 归母净利润 | `NPParentCompanyOwners` | ÷1e8 |

### 资产负债表 (zcfz)
| 分析需要 | API字段 | 注意 |
|---------|---------|------|
| 总资产 | `TotalAssets` | |
| 货币资金 | `CashEquivalents` | ⚠️这是现金及等价物，非全部货币资金 |
| 应收票据 | `BillAccReceivable` | |
| 其他应收款 | `OtherReceivableED` | |
| 预付账款 | `AdvancePayment` | |
| 存货 | `Inventories` | |
| 固定资产 | `TotalFixedAsset` | |
| 在建工程 | `TConstruInProcess` | |
| 无形资产 | `IntangibleAssets` | |
| 净资产 | `TotalShareholderEquity` | ⚠️索引18，不是17！ |
| 有息负债 | `InterestBearDebt` | API计算值，可能包含财务公司吸收存款 |
| 总负债 | `TotalLiability` | |
| 流动负债 | `TotalCurrentLiability` | |
| 流动资产 | `TotalCurrentAssets` | |
| 长期股权投资 | `LongtermEquityInvest` | |
| 交易性金融资产 | `TradingAssets` | |

### 现金流量表 (xjll)
| 分析需要 | API字段 |
|---------|---------|
| 经营现金流 | `NetOperateCashFlow` |
| 销售收现 | `GoodsSaleServiceRenderCash` |
| 投资现金流 | `NetInvestCashFlow` |
| 筹资现金流 | `NetFinanceCashFlow` |
| 资本开支 | ⚠️ 需从 mx-data 单独获取 `购建固定资产支付的现金` |
| 分红 | ⚠️ 需从 mx-data 单独获取 `分配股利支付的现金` |

---

## 图表规范速查

需生成约17张图表，详见 `chart-specs.md`。关键规范（v2.3）：

| 图表 | 类型 | v2.3规范 |
|------|------|---------|
| 营收+增长率 | 独立图：1柱+1线双Y轴 | 柱状图营收金额 + 折线图营收YoY |
| 净利润+增长率 | 独立图：1柱+1线双Y轴 | 柱状图净利金额 + 折线图净利YoY |
| 产品/业务收入构成 | 堆叠柱状图 | 展示各产品占比变化 |
| 地区收入构成 | 堆叠柱状图+折线 | 国内外收入 + 海外占比 |
| 费用率 | 🔴堆叠柱状图(stack)+毛利率右轴折线 | 销售+管理+研发堆叠=综合费用率 |
| ROE杜邦深度拆解 | 🔴并排柱状+折线单图 | 净利率/周转率/乘数=并排柱，ROE+毛利率=折线 |
| 资产结构饼图 | 🔴具体科目环形饼图 | 货币/应收/存货/固定/在建/无形/商誉等 |
| 负债结构饼图 | 🔴具体科目环形饼图 | 短借/长借/债券/应付/合同负债/薪酬 |
| OCF/资本开支/FCF | 🔴堆叠柱状图+FCF/OCF折线 | FCF(绿底)+Capex(红顶)=OCF |
| 安全性 | 双Y轴 | 现金/有息负债(柱)+流动比率(线) |
| 盈利能力 | 2柱+2线 | ROE+毛利率(柱)；净利率+费用率(线) |
| 成长性 | 2柱+2线 | 颜色显式指定 |
| 营运能力 | 双Y轴 | 柱状(应收+存货周转)；折线(固资+总资产周转) |

---

## 分析文字要求

每个图表必须配套分析文字，标准结构：
1. **数据陈述**：2-3句关键数据点
2. **趋势解读**：变化方向和幅度
3. **原因分析**：为什么变？（结合企业经营和行业背景）
4. **风险/机会判断**：这个变化意味着什么？

---

## 文件输出

```
公司研究/{公司简称}/
└── {公司简称}_企业分析_{YYYY-MM-DD}.html
```

---

## 参考资料

- `analysis-framework.md` — 完整分析框架（五轮四步法）
- `chart-specs.md` — 23-24张图表详细规格（含v2.2修订）
- `workflow.md` — 分步执行流程
- `references/anomaly-checklist.md` — 38条异常排查清单
- `references/roe-deep-dive.md` — ROE五层穿透分析
- `references/data-field-mapping.md` — API字段映射速查（⚠️ 必读）
- `references/lessons-learned.md` — 实战经验教训（⚠️ 必读）
- `references/calculation-formulas.md` — 所有计算指标公式汇总（v2.1新增）
