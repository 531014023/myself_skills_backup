#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报分析报告一键生成器 v1.0
============================
输入：westock-data 原始输出文件（zhsy/zcfz/xjll/kline）
输出：完整 ECharts HTML 交互式报告

用法（港股）：
  python report_builder.py \
    --code 00700 --name "腾讯控股" --market hk \
    --zhsy raw_zhsy.txt --zcfz raw_zcfz.txt --xjll raw_xjll.txt \
    --kline raw_kline.txt \
    --output "腾讯_企业分析.html"

用法（A股）：
  python report_builder.py \
    --code 600519 --name "贵州茅台" --market sh \
    --lrb raw_lrb.txt --zcfz raw_zcfz.txt --xjll raw_xjll.txt \
    --kline raw_kline.txt \
    --output "贵州茅台_企业分析.html"

设计原则：一次编写，永久复用。AI Agent 只需调用本脚本，无需手写代码。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# 第一部分：数据解析器 - 从 westock-data markdown 输出提取数据
# ============================================================

def parse_markdown_table(text, date_col='_date'):
    """
    解析 westock-data 输出的 markdown 表格
    返回: [{col: value, ...}, ...]
    """
    lines = text.strip().split('\n')
    # 找到表头行
    header_idx = -1
    for i, line in enumerate(lines):
        if '|' in line and date_col in line:
            header_idx = i
            break
    if header_idx < 0:
        raise ValueError(f"未找到表头行（含 {date_col}）")
    
    # 解析表头
    headers = [h.strip() for h in lines[header_idx].split('|') if h.strip()]
    # 跳过分隔行 (|---|---|...)
    rows = []
    for line in lines[header_idx + 2:]:
        if not line.strip() or '|' not in line:
            break
        cells = [c.strip() for c in line.split('|') if c.strip('|').strip() or c.strip() == '']
        # 去掉首尾空元素
        cells = [c for c in cells if c]
        if len(cells) >= len(headers):
            row = {}
            for j, h in enumerate(headers):
                val = cells[j] if j < len(cells) else ''
                row[h] = val
            rows.append(row)
    
    return rows


def filter_annual(rows, date_col='_date'):
    """从所有行中筛选年报（12-31）数据"""
    return [r for r in rows if '-12-31' in str(r.get(date_col, ''))]


def safe_float(val):
    """安全转换为浮点数"""
    if val is None or val == '' or val == '-' or val == '--':
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def e8(val):
    """转换为亿单位"""
    return safe_float(val) / 1e8


# ============================================================
# 港股字段映射（westock-data raw → 内部标准格式）
# ============================================================

HK_FIELD_MAP = {
    # 综合损益表 zhsy
    "zhsy": {
        "operating_revenue": "OperatingIncome",
        "gross_margin_pct": "GrossIncomeRatio",
        "net_margin_pct": "NetProfitRatio",
        "roe_pct": "RoeWeighted",
        "eps": "BasicEPS",
        "sell_expense": "SalesExpense",
        "admin_expense": "AdministrationExpense",
        "finance_expense": "FinancialCost",
        "operating_profit": "OperatingProfit",
        "profit_to_shareholders": "ProfitToShareholders",
        "tax": "Tax",
        "oper_expenses": "OperExpenses",
        "rev_growth": "OperatingRevenueGr1y",
        "profit_growth": "NetProfitGr1y",
        "asset_turnover": "TotalAssetTRate",
    },
    # 资产负债表 zcfz
    "zcfz": {
        "total_assets": "TotalAssets",
        "current_assets": "TotalCurrentAssets",
        "cash": "Cash",
        "fixed_assets": "FixedAssets",
        "construction": "ConstruInProcess",
        "intangible_assets": "IntangibleAssets",
        "receivables": "TotalAccountReceivable",
        "inventory": "Inventories",
        "long_term_loan": "LongTermLoan",
        "total_equity": "TotalEquity",
        "parent_equity": "SeWithoutMinority",
        "total_liability": "TotalLiability",
        "current_liability": "TotalCurrentLiability",
    },
    # 现金流量表 xjll
    "xjll": {
        "cfo": "CFO",
        "cfi": "CFI",
        "cff": "CFF",
        "sales_cash": "CashReceiptsfope",
        "capex": "Purcapitalassents",
        "dividend_paid": "Dividendinterestpayment",
    },
}


def parse_hk_finance(filepath, stmt_type):
    """解析港股 westock-data 原始输出文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    all_rows = parse_markdown_table(text)
    annual_rows = filter_annual(all_rows)
    
    field_map = HK_FIELD_MAP[stmt_type]
    result = {}
    for key, api_field in field_map.items():
        result[key] = [e8(r.get(api_field, '0')) for r in annual_rows]
    
    result["years"] = [int(r['_date'].split('-')[0]) for r in annual_rows]
    return result


def parse_kline(filepath):
    """解析K线数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    rows = parse_markdown_table(text, date_col='date')
    # 取年末数据（12-31），或每年最后一条
    prices = {}
    for r in rows:
        try:
            d = r.get('date', '')
            if '12-31' in d or '12-30' in d or '12-29' in d:
                year = int(d.split('-')[0])
                close = safe_float(r.get('last', r.get('close', '0')))
                if close > 0:  # 过滤异常负值
                    prices[year] = close
        except:
            continue
    
    # 按年份排序
    sorted_years = sorted(prices.keys())
    return {
        "years": sorted_years,
        "prices": [prices[y] for y in sorted_years],
    }


# ============================================================
# 第二部分：指标计算器
# ============================================================

def calc_indicators(income, balance, cashflow):
    """根据三表数据计算所有衍生指标"""
    n = len(income["years"])
    ind = {}
    
    # === 增长率 ===
    ind["rev_growth"] = [None] + [
        (income["operating_revenue"][i] / income["operating_revenue"][i-1] - 1) * 100
        for i in range(1, n)
    ]
    ind["profit_growth"] = [None] + [
        (income["profit_to_shareholders"][i] / income["profit_to_shareholders"][i-1] - 1) * 100
        for i in range(1, n)
    ]
    ind["asset_growth"] = [None] + [
        (balance["total_assets"][i] / balance["total_assets"][i-1] - 1) * 100
        for i in range(1, n)
    ]
    ind["equity_growth"] = [None] + [
        (balance["total_equity"][i] / balance["total_equity"][i-1] - 1) * 100
        for i in range(1, n)
    ]
    
    # === 负债指标 ===
    ind["debt_ratio"] = [
        balance["long_term_loan"][i] / balance["total_assets"][i] * 100
        for i in range(n)
    ]
    ind["cash_debt_ratio"] = [
        balance["cash"][i] / balance["long_term_loan"][i] if balance["long_term_loan"][i] > 0 else 999
        for i in range(n)
    ]
    ind["liability_ratio"] = [
        balance["total_liability"][i] / balance["total_assets"][i] * 100
        for i in range(n)
    ]
    
    # === 流动性 ===
    ind["current_ratio"] = [
        balance["current_assets"][i] / balance["current_liability"][i]
        for i in range(n)
    ]
    ind["quick_ratio"] = [
        (balance["current_assets"][i] - balance["inventory"][i]) / balance["current_liability"][i]
        for i in range(n)
    ]
    
    # === 现金流 ===
    ind["ocf_profit"] = [
        cashflow["cfo"][i] / income["profit_to_shareholders"][i]
        for i in range(n)
    ]
    ind["cash_rev"] = [
        cashflow["sales_cash"][i] / income["operating_revenue"][i]
        for i in range(n)
    ]
    ind["fcf"] = [
        cashflow["cfo"][i] - cashflow["capex"][i]
        for i in range(n)
    ]
    ind["cash_total_debt"] = [
        balance["cash"][i] / balance["total_liability"][i] * 100
        for i in range(n)
    ]
    
    # === 费用率 ===
    ind["fee_rate"] = [
        (abs(income["sell_expense"][i]) + abs(income["admin_expense"][i])) / income["operating_revenue"][i] * 100
        for i in range(n)
    ]
    
    # === 资产结构 ===
    ind["prod_asset"] = [
        balance["fixed_assets"][i] + balance["construction"][i] + balance["intangible_assets"][i] * 0.3
        for i in range(n)
    ]
    ind["prod_asset_ratio"] = [
        ind["prod_asset"][i] / balance["total_assets"][i] * 100
        for i in range(n)
    ]
    ind["receivable_ratio"] = [
        balance["receivables"][i] / balance["total_assets"][i] * 100
        for i in range(n)
    ]
    
    # 非主业资产（粗估：总资产 - 现金 - 存货 - 应收 - 固定 - 在建）
    ind["non_core_ratio"] = [
        100 - (balance["cash"][i] + balance["inventory"][i] + balance["receivables"][i]
               + balance["fixed_assets"][i] + balance["construction"][i]) / balance["total_assets"][i] * 100
        for i in range(n)
    ]
    
    # === 周转率 ===
    ind["asset_turnover"] = [
        income["operating_revenue"][i] / balance["total_assets"][i]
        for i in range(n)
    ]
    ind["fixed_asset_turnover"] = [
        income["operating_revenue"][i] / balance["fixed_assets"][i] if balance["fixed_assets"][i] > 0 else 0
        for i in range(n)
    ]
    ind["receivable_turnover"] = [
        income["operating_revenue"][i] / balance["receivables"][i] if balance["receivables"][i] > 0 else 0
        for i in range(n)
    ]
    ind["inventory_turnover"] = [
        income["operating_revenue"][i] / balance["inventory"][i] if balance["inventory"][i] > 0 else 9999
        for i in range(n)
    ]
    
    # === ROA ===
    ind["roa"] = [
        income["profit_to_shareholders"][i] / balance["total_assets"][i] * 100
        for i in range(n)
    ]
    
    # === 杜邦因子 ===
    ind["dupont_npm"] = [income["net_margin_pct"][i] for i in range(n)]
    ind["dupont_turnover"] = [ind["asset_turnover"][i] for i in range(n)]
    ind["dupont_equity_mult"] = [
        balance["total_assets"][i] / balance["total_equity"][i]
        for i in range(n)
    ]
    
    return ind


# ============================================================
# 第三部分：HTML 报告生成器
# ============================================================

COLORS = {
    "revenue": "#C23531", "netProfit": "#2F4554", "stockPrice": "#C23531",
    "grossMargin": "#61A0A8", "netMargin": "#D48265", "feeRate": "#91C7AE",
    "cashFlow": "#CA8622", "salesCash": "#BDA29A", "liabilities": "#6E7074",
    "cashBalance": "#749F83", "investOut": "#C23531", "dividend": "#546570",
    "roe": "#C23531", "asset": "#61A0A8", "equity": "#91C7AE",
}

def js_arr(arr, fmt=None):
    """将 Python 数组转为 JS 数组字符串"""
    vals = []
    for x in arr:
        if x is None:
            vals.append("null")
        elif fmt and isinstance(x, float):
            vals.append(f"{x:{fmt}}")
        else:
            vals.append(json.dumps(x))
    return "[" + ", ".join(vals) + "]"


class ReportGenerator:
    """通用财报报告生成器"""
    
    def __init__(self, company_name, stock_code, market="hk"):
        self.name = company_name
        self.code = stock_code
        self.market = market
        self.currency = "港元" if market == "hk" else "元"
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        
    def build(self, income, balance, cashflow, indicators, stock_prices, products=None):
        """生成完整HTML报告"""
        self.income = income
        self.balance = balance
        self.cashflow = cashflow
        self.ind = indicators
        self.stock = stock_prices
        self.products = products or {}
        self.years = income["years"]
        self.n = len(self.years)
        
        html = self._build_html()
        return html
    
    def _build_html(self):
        """构建完整HTML"""
        y = json.dumps(self.years)
        rev = js_arr(self.income["operating_revenue"], ".4g")
        profit = js_arr(self.income["profit_to_shareholders"], ".4g")
        rg = js_arr(self.ind["rev_growth"], ".3g")
        pg = js_arr(self.ind["profit_growth"], ".3g")
        roe = js_arr(self.income["roe_pct"], ".3g")
        gm = js_arr(self.income["gross_margin_pct"], ".3g")
        nm = js_arr(self.income["net_margin_pct"], ".3g")
        npm = js_arr(self.ind["dupont_npm"], ".3g")
        turnover = js_arr([round(x, 3) for x in self.ind["dupont_turnover"]])
        em = js_arr([round(x, 2) for x in self.ind["dupont_equity_mult"]])
        fr = js_arr([round(x, 1) for x in self.ind["fee_rate"]])
        roa = js_arr([round(x, 1) for x in self.ind["roa"]])
        
        cfo = js_arr(self.cashflow["cfo"], ".4g")
        cfi = js_arr(self.cashflow["cfi"], ".4g")
        cff = js_arr(self.cashflow["cff"], ".4g")
        cap = js_arr(self.cashflow["capex"], ".4g")
        div = js_arr(self.cashflow["dividend_paid"], ".4g")
        fcf = js_arr(self.ind["fcf"], ".4g")
        ocf_profit = js_arr([round(x, 2) for x in self.ind["ocf_profit"]])
        cash_rev = js_arr([round(x, 2) for x in self.ind["cash_rev"]])
        
        cash = js_arr(self.balance["cash"], ".4g")
        debt = js_arr(self.balance["long_term_loan"], ".4g")
        dr = js_arr([round(x, 1) for x in self.ind["debt_ratio"]])
        pr = js_arr([round(x, 1) for x in self.ind["prod_asset_ratio"]])
        rr = js_arr([round(x, 1) for x in self.ind["receivable_ratio"]])
        nr = js_arr([round(x, 1) for x in self.ind["non_core_ratio"]])
        lr = js_arr([round(x, 1) for x in self.ind["liability_ratio"]])
        cr = js_arr([round(x, 2) for x in self.ind["current_ratio"]])
        cdr = js_arr([round(x, 2) for x in self.ind["cash_debt_ratio"]])
        ctd = js_arr([round(x, 1) for x in self.ind["cash_total_debt"]])
        
        ag = js_arr(self.ind["asset_growth"], ".3g")
        eg = js_arr(self.ind["equity_growth"], ".3g")
        
        art = js_arr([round(x, 1) for x in self.ind["receivable_turnover"]])
        at = js_arr([round(x, 2) for x in self.ind["asset_turnover"]])
        invt = js_arr([round(x, 0) for x in self.ind["inventory_turnover"]])
        fat = js_arr([round(x, 1) for x in self.ind["fixed_asset_turnover"]])
        
        stock_y = js_arr(self.stock["years"])
        stock_p = js_arr(self.stock["prices"], ".4g")
        
        # 产品构成图数据
        product_js = json.dumps(self.products) if self.products else "null"
        
        # 资产结构饼图（最新一期）
        last = self.n - 1
        ta_last = self.balance["total_assets"][last]
        cash_last = self.balance["cash"][last]
        fa_last = self.balance["fixed_assets"][last]
        cip_last = self.balance["construction"][last]
        ia_last = self.balance["intangible_assets"][last]
        ar_last = self.balance["receivables"][last]
        inv_last = self.balance["inventory"][last]
        other_last = ta_last - cash_last - fa_last - cip_last - ia_last - ar_last - inv_last
        
        # 现金流肖像表
        portrait_rows = []
        for i, yr in enumerate(self.years):
            cf1 = "+" if self.cashflow["cfo"][i] > 0 else "-"
            cf2 = "+" if self.cashflow["cfi"][i] > 0 else "-"
            cf3 = "+" if self.cashflow["cff"][i] > 0 else "-"
            pattern = cf1 + cf2 + cf3
            type_map = {
                "+++": "妖精型", "++-": "老母鸡型", "+-+": "蛮牛型", "+--": "奶牛型",
                "---": "大出血型", "--+": "赌徒型", "-+-": "混吃等死型", "-++": "骗吃骗喝型"
            }
            ptype = type_map.get(pattern, "?")
            portrait_rows.append(
                f'<tr><td>{yr}</td>'
                f'<td class="{"pos" if cf1 == "+" else "neg"}">{cf1}</td>'
                f'<td class="{"pos" if cf2 == "+" else "neg"}">{cf2}</td>'
                f'<td class="{"pos" if cf3 == "+" else "neg"}">{cf3}</td>'
                f'<td class="type-label">{ptype}</td></tr>'
            )
        
        # 最新数据快速参考
        last_rev = self.income["operating_revenue"][last]
        last_np = self.income["profit_to_shareholders"][last]
        last_roe = self.income["roe_pct"][last]
        last_gm = self.income["gross_margin_pct"][last]
        last_ocf = self.cashflow["cfo"][last]
        last_ratio = self.ind["ocf_profit"][last]
        last_liar = self.ind["liability_ratio"][last]
        rev_g = self.ind["rev_growth"][last]
        np_g = self.ind["profit_growth"][last]
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.name}({self.code}) 深度财务分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; }}
.report-header {{ background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); color: #fff; padding: 40px 60px; }}
.report-header h1 {{ font-size: 32px; margin-bottom: 8px; }}
.report-header .subtitle {{ font-size: 16px; opacity: 0.85; }}
.report-header .meta {{ font-size: 13px; opacity: 0.7; margin-top: 12px; }}
.report-header .info-box {{ background: rgba(255,255,255,.1); border-radius: 8px; padding: 16px; margin-top: 16px; font-size: 13px; border-left: 4px solid #61A0A8; }}
.sidebar {{ position: fixed; left: 0; top: 0; width: 240px; height: 100vh; background: #1a1a2e; color: #ccc; overflow-y: auto; padding: 20px 0; z-index: 100; font-size: 13px; }}
.sidebar .nav-title {{ padding: 12px 20px; font-weight: bold; color: #fff; border-bottom: 1px solid rgba(255,255,255,.1); }}
.sidebar a {{ display: block; padding: 8px 20px; color: #aaa; text-decoration: none; transition: .2s; }}
.sidebar a:hover {{ color: #fff; background: rgba(255,255,255,.05); }}
.sidebar a.round {{ padding-left: 28px; font-weight: 600; color: #61A0A8; margin-top: 12px; border-top: 1px solid rgba(255,255,255,.05); }}
.main {{ margin-left: 240px; padding: 30px 40px; max-width: 1200px; }}
.section-title {{ font-size: 24px; font-weight: 700; margin: 40px 0 20px; padding-bottom: 10px; border-bottom: 3px solid #C23531; color: #1a1a2e; }}
.card {{ background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,.06); }}
.card h3 {{ font-size: 17px; color: #1a1a2e; margin-bottom: 16px; padding-left: 12px; border-left: 4px solid #C23531; }}
.chart {{ width: 100%; }}
.analysis {{ background: #f8fafc; border-radius: 8px; padding: 16px; margin-top: 16px; font-size: 14px; line-height: 1.8; color: #444; border-left: 3px solid #61A0A8; }}
.analysis strong {{ color: #C23531; }}
table.pdata {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }}
table.pdata th, table.pdata td {{ padding: 8px 12px; text-align: center; border: 1px solid #e0e0e0; }}
table.pdata th {{ background: #1a1a2e; color: #fff; }}
table.pdata .pos {{ background: #e8f5e9; }}
table.pdata .neg {{ background: #ffeaea; }}
.summary {{ background: linear-gradient(135deg, #fff5f5, #fff); border: 1px solid #fecaca; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
.summary h3 {{ color: #C23531; margin-bottom: 12px; }}
.summary ul {{ list-style: none; padding: 0; }}
.summary li {{ padding: 6px 0; border-bottom: 1px dashed #eee; }}
.summary li:last-child {{ border-bottom: none; }}
.green {{ color: #2e7d32; }}
.red {{ color: #C23531; }}
@media print {{ .sidebar {{ display: none; }} .main {{ margin-left: 0; }} }}
</style>
</head>
<body>

<nav class="sidebar">
<div class="nav-title">分析目录</div>
<a href="#s1" class="round">第一轮：鸟瞰概览</a>
<a href="#s1-1">1.1 公司基本信息</a>
<a href="#s1-2">1.2 股价历史</a>
<a href="#s1-3">1.3 营收历史</a>
<a href="#s1-4">1.4 净利润历史</a>
<a href="#s2" class="round">第二轮：结构拆解</a>
<a href="#s2-1">2.1 ROE杜邦分析</a>
<a href="#s2-2">2.2 资产结构</a>
<a href="#s2-3">2.3 现金流肖像</a>
<a href="#s3" class="round">第三轮：排雷检查</a>
<a href="#s3-1">3.1 安全性</a>
<a href="#s3-2">3.2 盈利能力</a>
<a href="#s3-3">3.3 成长性</a>
<a href="#s3-4">3.4 营运能力</a>
<a href="#s3-5">3.5 OCF/FCF/CapEx</a>
<a href="#s3-6">3.6 资产负债趋势</a>
<a href="#s3-7">3.7 利润vs现金流</a>
<a href="#s3-8">3.8 产品构成</a>
<a href="#s4" class="round">第四轮：综合评估</a>
<a href="#s5" class="round">第五轮：结论</a>
</nav>

<main class="main">

<header class="report-header">
<h1>{self.name} ({self.code})</h1>
<div class="subtitle">深度财务分析报告 — 唐朝《手把手教你读财报》方法论</div>
<div class="meta">分析日期：{self.report_date} | 数据截至：{self.years[-1]}年报 | 货币：{self.currency}</div>
<div class="info-box">
<strong>数据来源：</strong>westock-data API（三表主数据 + K线），覆盖 {self.years[0]}-{self.years[-1]} 年报。<br>
<strong>报告生成器：</strong>report_builder.py v1.0 | 分析框架参考唐朝《手把手教你读财报2021》
</div>
</header>

<!-- ===== 第一轮 ===== -->
<div class="section-title" id="s1">第一轮：鸟瞰概览</div>

<div class="card" id="s1-1">
<h3>1.1 公司基本信息</h3>
<table style="width:100%; border-collapse:collapse; font-size:14px;">
<tr><td style="padding:8px; color:#666; width:120px;">公司名称</td><td style="padding:8px; font-weight:600;">{self.name}</td>
<td style="padding:8px; color:#666; width:120px;">股票代码</td><td style="padding:8px; font-weight:600;">{self.code}</td></tr>
<tr><td style="padding:8px; color:#666;">{self.years[-1]}营收</td><td style="padding:8px; font-weight:600;">{last_rev:.0f}亿{self.currency}</td>
<td style="padding:8px; color:#666;">{self.years[-1]}净利</td><td style="padding:8px; font-weight:600;">{last_np:.0f}亿{self.currency}</td></tr>
<tr><td style="padding:8px; color:#666;">{self.years[-1]}ROE</td><td style="padding:8px; font-weight:600;">{last_roe:.1f}%</td>
<td style="padding:8px; color:#666;">毛利率</td><td style="padding:8px; font-weight:600;">{last_gm:.1f}%</td></tr>
<tr><td style="padding:8px; color:#666;">经营现金流</td><td style="padding:8px; font-weight:600;" class="green">{last_ocf:.0f}亿</td>
<td style="padding:8px; color:#666;">OCF/NI</td><td style="padding:8px; font-weight:600;" class="green">{last_ratio:.2f}x</td></tr>
</table>
</div>

<div class="card" id="s1-2">
<h3>1.2 股价历史走势（年末收盘价·{self.currency}）</h3>
<div class="chart" id="ch_stock" style="height:400px;"></div>
<div class="analysis"><strong>数据展示：</strong>股价从 {self.stock["years"][0]} 年 {self.stock["prices"][0]:.1f}{self.currency} 至 {self.years[-1]} 年 {self.stock["prices"][-1]:.1f}{self.currency}。<strong>（请根据实际股价走势补充分析文字）</strong></div>
</div>

<div class="card" id="s1-3">
<h3>1.3 营收历史</h3>
<div class="chart" id="ch_rev" style="height:400px;"></div>
<div class="analysis"><strong>营收：</strong>从 {self.years[0]} 年 {self.income["operating_revenue"][0]:.0f}亿增长至 {self.years[-1]} 年 {last_rev:.0f}亿，最新一年同比 {rev_g:.1f}%。<strong>（请根据实际数据补充分析）</strong></div>
</div>

<div class="card" id="s1-4">
<h3>1.4 净利润历史</h3>
<div class="chart" id="ch_profit" style="height:400px;"></div>
<div class="analysis"><strong>净利润：</strong>从 {self.years[0]} 年 {self.income["profit_to_shareholders"][0]:.0f}亿增至 {last_np:.0f}亿，最新同比 {np_g:.1f}%。<strong>（请根据实际数据补充分析）</strong></div>
</div>

<!-- ===== 第二轮 ===== -->
<div class="section-title" id="s2">第二轮：结构拆解</div>

<div class="card" id="s2-1">
<h3>2.1 ROE杜邦深度拆解</h3>
<div class="chart" id="ch_roe" style="height:800px;"></div>
<div class="analysis"><strong>ROE趋势：</strong>从 {self.income["roe_pct"][0]:.1f}% 变化至 {last_roe:.1f}%。杜邦拆解：净利率({self.ind["dupont_npm"][last]:.1f}%) × 周转率({self.ind["dupont_turnover"][last]:.2f}次) × 权益乘数({self.ind["dupont_equity_mult"][last]:.1f}倍)。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s2-2">
<h3>2.2 资产结构（{self.years[-1]}年末）</h3>
<div class="chart" id="ch_asset" style="height:400px;"></div>
<div class="analysis"><strong>总资产：</strong>{ta_last:.0f}亿{self.currency}。生产资产占比 {self.ind["prod_asset_ratio"][last]:.1f}%，应收占总资产 {self.ind["receivable_ratio"][last]:.1f}%。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s2-3">
<h3>2.3 现金流肖像</h3>
<div class="chart" id="ch_cf" style="height:400px;"></div>
<table class="pdata">
<tr><th>年份</th><th>经营CF</th><th>投资CF</th><th>筹资CF</th><th>类型</th></tr>
{"".join(portrait_rows)}
</table>
<div class="analysis"><strong>现金流演变：</strong><strong>（请根据现金流肖像表补充分析）</strong></div>
</div>

<!-- ===== 第三轮 ===== -->
<div class="section-title" id="s3">第三轮：排雷检查</div>

<div class="card" id="s3-1">
<h3>3.1 安全性分析</h3>
<div class="chart" id="ch_safety" style="height:450px;"></div>
<div class="analysis"><strong>资产负债率：</strong>{last_liar:.1f}%。现金/有息负债：{self.ind["cash_debt_ratio"][last]:.2f}。流动比率：{self.ind["current_ratio"][last]:.2f}。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s3-2">
<h3>3.2 盈利能力</h3>
<div class="chart" id="ch_profitability" style="height:450px;"></div>
<div class="analysis"><strong>毛利率：</strong>{last_gm:.1f}%。<strong>净利率：</strong>{self.income["net_margin_pct"][last]:.1f}%。<strong>ROE：</strong>{last_roe:.1f}%。<strong>费用率：</strong>{self.ind["fee_rate"][last]:.1f}%。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s3-3">
<h3>3.3 成长性</h3>
<div class="chart" id="ch_growth" style="height:450px;"></div>
<div class="analysis"><strong>营收增速：</strong>最新 {rev_g:.1f}%。<strong>净利增速：</strong>最新 {np_g:.1f}%。<strong>资产增速：</strong>{self.ind["asset_growth"][last]:.1f}%。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s3-4">
<h3>3.4 营运能力</h3>
<div class="chart" id="ch_operation" style="height:450px;"></div>
<div class="analysis"><strong>应收周转率：</strong>{self.ind["receivable_turnover"][last]:.1f}次。<strong>总资产周转率：</strong>{self.ind["asset_turnover"][last]:.2f}次。<strong>固定资产周转率：</strong>{self.ind["fixed_asset_turnover"][last]:.1f}次。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s3-5">
<h3>3.5 OCF / 资本开支 / 自由现金流</h3>
<div class="chart" id="ch_ocf" style="height:400px;"></div>
<div class="analysis"><strong>FCF：</strong>{self.ind["fcf"][last]:.0f}亿{self.currency}。<strong>CapEx/OCF：</strong>{self.cashflow["capex"][last]/self.cashflow["cfo"][last]*100:.1f}%。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s3-6">
<h3>3.6 资产负债关键比率趋势</h3>
<div class="chart" id="ch_bs" style="height:450px;"></div>
<div class="analysis"><strong>（请根据图表补充分析）</strong></div>
</div>

<div class="card" id="s3-7">
<h3>3.7 净利润 vs 经营现金流</h3>
<div class="chart" id="ch_np_ocf" style="height:400px;"></div>
<div class="analysis"><strong>OCF/NI：</strong>10年均值 {sum(self.ind["ocf_profit"])/self.n:.2f}x，最新 {last_ratio:.2f}x。<strong>利润含金量判断：</strong>{'优' if last_ratio >= 1.0 else '需关注'}。<strong>（请补充分析）</strong></div>
</div>

<div class="card" id="s3-8">
<h3>3.8 产品/收入构成</h3>
<div class="chart" id="ch_product" style="height:450px;"></div>
<div class="analysis"><strong>（请根据产品构成图表补充分析）</strong></div>
</div>

<!-- ===== 第四轮 ===== -->
<div class="section-title" id="s4">第四轮：综合评估</div>

<div class="card">
<h3>4.1 现金流画像总结</h3>
<div class="analysis"><strong>（请根据现金流肖像表总结公司现金流演变特征）</strong></div>
</div>

<div class="card">
<h3>4.2 优质企业五组数据检验</h3>
<table style="width:100%; border-collapse:collapse; font-size:13px;">
<tr style="background:#f0f4f8;"><th style="padding:10px;">#</th><th style="padding:10px;">检验标准</th><th style="padding:10px;">{self.years[-1]}年数据</th><th style="padding:10px;">结论</th></tr>
<tr><td style="padding:10px;">1</td><td style="padding:10px;">经营现金流 > 净利润 > 0</td>
<td style="padding:10px;" class="green">{last_ocf:.0f}亿 > {last_np:.0f}亿 > 0</td>
<td style="padding:10px;">{'✅ 通过' if last_ratio >= 1.0 else '⚠️ 关注'}</td></tr>
<tr><td style="padding:10px;">2</td><td style="padding:10px;">销售收现 >= 营收</td>
<td style="padding:10px;">{self.cashflow["sales_cash"][last]:.0f}亿 vs {last_rev:.0f}亿</td>
<td style="padding:10px;">{'✅ 通过' if self.ind["cash_rev"][last] >= 0.9 else '⚠️ 需核实'}</td></tr>
<tr><td style="padding:10px;">3</td><td style="padding:10px;">投资流出 > 流入（扩张中）</td>
<td style="padding:10px;">出{abs(self.cashflow["cfi"][last]):.0f}亿</td>
<td style="padding:10px;">{'✅ 通过' if self.cashflow["cfi"][last] < 0 else '⚠️'}</td></tr>
<tr><td style="padding:10px;">4</td><td style="padding:10px;">期末现金 >= 有息负债</td>
<td style="padding:10px;">{cash_last:.0f}亿 vs {self.balance["long_term_loan"][last]:.0f}亿</td>
<td style="padding:10px;">{'✅ 通过' if self.ind["cash_debt_ratio"][last] >= 1.0 else '⚠️ 未通过'}</td></tr>
<tr><td style="padding:10px;">5</td><td style="padding:10px;">应收/总资产 < 30%</td>
<td style="padding:10px;">{self.ind["receivable_ratio"][last]:.1f}%</td>
<td style="padding:10px;">✅ 通过</td></tr>
</table>
</div>

<!-- ===== 第五轮 ===== -->
<div class="section-title" id="s5">第五轮：结论</div>

<div class="card">
<h3>5.1 核心数据摘要</h3>
<div class="analysis">
<strong>{self.years[-1]}年关键数据：</strong><br>
营收 {last_rev:.0f}亿{self.currency} | 净利 {last_np:.0f}亿 | ROE {last_roe:.1f}%<br>
毛利率 {last_gm:.1f}% | 净利率 {self.income["net_margin_pct"][last]:.1f}% | 资产负债率 {last_liar:.1f}%<br>
经营现金流 {last_ocf:.0f}亿 | OCF/NI {last_ratio:.2f}x | 资本开支 {self.cashflow["capex"][last]:.0f}亿<br><br>
<strong>（请在此补充综合结论和分析判断）</strong><br><br>
<span style="font-size:12px; color:#999;">⚠️ 免责声明：本报告仅基于公开财务数据分析，不构成任何投资建议。投资有风险，入市需谨慎。</span>
</div>
</div>

</main>

<script>
(function(){{

// === Chart 1: 股价 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_stock'));
  c.setOption({{
    title: {{ text: '股价历史（年末收盘价·{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {stock_y} }},
    yAxis: {{ type: 'value', name: '{self.currency}' }},
    series: [{{
      type: 'line', data: {stock_p}, smooth: true,
      lineStyle: {{ color: '#C23531', width: 3 }},
      itemStyle: {{ color: '#C23531' }}, symbol: 'circle', symbolSize: 8,
      areaStyle: {{ color: {{ type: 'linear', x:0, y:0, x2:0, y2:1,
        colorStops: [{{offset:0, color:'rgba(194,53,49,.25)'}},{{offset:1, color:'rgba(194,53,49,.02)'}}] }}
      }}
    }}]
  }});
}})();

// === Chart 2: 营收 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_rev'));
  c.setOption({{
    title: {{ text: '营业收入（亿{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '亿{self.currency}' }},
    series: [{{
      type: 'bar', data: {rev},
      itemStyle: {{ color: '#C23531', borderRadius: [6,6,0,0] }},
      label: {{ show: true, position: 'top', formatter: function(p) {{
        var g = {rg}; return p.dataIndex > 0 && g[p.dataIndex] ? g[p.dataIndex].toFixed(1)+'%' : '';
      }}, fontSize: 11 }}
    }}]
  }});
}})();

// === Chart 3: 净利润 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_profit'));
  c.setOption({{
    title: {{ text: '归母净利润（亿{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '亿{self.currency}' }},
    series: [{{
      type: 'bar', data: {profit},
      itemStyle: {{ color: '#2F4554', borderRadius: [6,6,0,0] }},
      label: {{ show: true, position: 'top', formatter: function(p) {{
        var g = {pg}; return p.dataIndex > 0 && g[p.dataIndex] ? g[p.dataIndex].toFixed(1)+'%' : '';
      }}, fontSize: 11 }}
    }}]
  }});
}})();

// === Chart 4: ROE杜邦 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_roe'));
  c.setOption({{
    title: {{ text: 'ROE杜邦深度拆解', left: 'center', textStyle: {{fontSize:14}} }},
    grid: [
      {{ left: '7%', right: '7%', top: '8%', height: '22%' }},
      {{ left: '7%', right: '7%', top: '35%', height: '22%' }},
      {{ left: '7%', right: '7%', top: '62%', height: '35%' }}
    ],
    xAxis: [
      {{ type: 'category', data: {y}, gridIndex: 0 }},
      {{ type: 'category', data: {y}, gridIndex: 1 }},
      {{ type: 'category', data: {y}, gridIndex: 2 }}
    ],
    yAxis: [
      {{ type: 'value', name: '%', gridIndex: 0 }},
      {{ type: 'value', name: '次/倍数', gridIndex: 1 }},
      {{ type: 'value', name: '%', gridIndex: 2 }}
    ],
    series: [
      {{ name: 'ROE(%)', type: 'line', data: {roe}, xAxisIndex:0, yAxisIndex:0,
        lineStyle: {{ color: '#C23531', width: 3 }}, symbol: 'circle', symbolSize: 8,
        markLine: {{ silent:true, data:[{{ yAxis:20, lineStyle:{{color:'#999',type:'dashed'}}, label:{{formatter:'20%'}} }}] }}
      }},
      {{ name: '净利率(%)', type: 'line', data: {nm}, xAxisIndex:0, yAxisIndex:0,
        lineStyle: {{ color: '#D48265', type: 'dashed' }}, symbol: 'none' }},
      {{ name: '周转率(次)', type: 'line', data: {turnover}, xAxisIndex:1, yAxisIndex:1,
        lineStyle: {{ color: '#61A0A8' }}, symbol: 'diamond', symbolSize: 8 }},
      {{ name: '权益乘数', type: 'line', data: {em}, xAxisIndex:1, yAxisIndex:1,
        lineStyle: {{ color: '#91C7AE', type: 'dashed' }}, symbol: 'triangle', symbolSize: 8 }},
      {{ name: '毛利率(%)', type: 'line', data: {gm}, xAxisIndex:2, yAxisIndex:2,
        lineStyle: {{ color: '#61A0A8', width: 2.5 }}, symbol: 'none' }},
      {{ name: '费用率(%)', type: 'line', data: {fr}, xAxisIndex:2, yAxisIndex:2,
        lineStyle: {{ color: '#91C7AE' }}, symbol: 'diamond', symbolSize: 6,
        areaStyle: {{ color: 'rgba(145,199,174,.3)' }} }},
      {{ name: '净利率(%)', type: 'line', data: {nm}, xAxisIndex:2, yAxisIndex:2,
        lineStyle: {{ color: '#D48265' }}, symbol: 'circle', symbolSize: 7 }},
    ]
  }});
}})();

// === Chart 5: 资产结构饼图 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_asset'));
  c.setOption({{
    title: {{ text: '{self.years[-1]}年资产结构（总资产 {ta_last:.0f}亿{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}}亿({self.currency} ({{d}}%)' }},
    series: [{{
      type: 'pie', radius: ['40%','70%'],
      data: [
        {{ value:{cash_last:.1f}, name:'货币资金', itemStyle:{{color:'#749F83'}} }},
        {{ value:{fa_last:.1f}, name:'固定资产', itemStyle:{{color:'#C23531'}} }},
        {{ value:{cip_last:.1f}, name:'在建工程', itemStyle:{{color:'#E69D87'}} }},
        {{ value:{ia_last:.1f}, name:'无形资产', itemStyle:{{color:'#61A0A8'}} }},
        {{ value:{ar_last:.1f}, name:'应收账款', itemStyle:{{color:'#BDA29A'}} }},
        {{ value:{inv_last:.1f}, name:'存货', itemStyle:{{color:'#91C7AE'}} }},
        {{ value:{max(0, other_last):.1f}, name:'其他资产(含投资等)', itemStyle:{{color:'#6E7074'}} }}
      ],
      label: {{ formatter: '{{b}}\\n{{d}}%' }}
    }}]
  }});
}})();

// === Chart 6: 现金流 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_cf'));
  c.setOption({{
    title: {{ text: '三大现金流（亿{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['经营CF','投资CF','筹资CF'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '亿{self.currency}' }},
    series: [
      {{ name: '经营CF', type: 'bar', data: {cfo}, itemStyle: {{ color: '#2e7d32', borderRadius:[4,4,0,0] }} }},
      {{ name: '投资CF', type: 'bar', data: {cfi}, itemStyle: {{ color: '#C23531', borderRadius:[4,4,0,0] }} }},
      {{ name: '筹资CF', type: 'bar', data: {cff}, itemStyle: {{ color: '#1565C0', borderRadius:[4,4,0,0] }} }}
    ]
  }});
}})();

// === Chart 7: 安全性 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_safety'));
  c.setOption({{
    title: {{ text: '安全性指标', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['现金/有息负债','流动比率','资产负债率%','有息负债率%','现金/总负债%'], bottom:0, type:'scroll' }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: [{{ type: 'value', name: '比率' }}, {{ type: 'value', name: '%' }}],
    series: [
      {{ name: '现金/有息负债', type: 'bar', data: {cdr}, yAxisIndex:0,
        itemStyle: {{ color: '#749F83' }},
        markLine: {{ silent:true, data:[{{ yAxis:1.0, lineStyle:{{color:'#C23531',type:'dashed'}}, label:{{formatter:'安全线1.0'}} }}] }}
      }},
      {{ name: '流动比率', type: 'line', data: {cr}, yAxisIndex:0,
        lineStyle: {{ color: '#1565C0' }}, symbol: 'diamond', symbolSize: 8 }},
      {{ name: '资产负债率%', type: 'line', data: {lr}, yAxisIndex:1,
        lineStyle: {{ color: '#6E7074', type: 'dashed' }}, symbol: 'triangle', symbolSize: 8 }},
      {{ name: '有息负债率%', type: 'line', data: {dr}, yAxisIndex:1,
        lineStyle: {{ color: '#C23531' }}, symbol: 'none' }},
      {{ name: '现金/总负债%', type: 'line', data: {ctd}, yAxisIndex:1,
        lineStyle: {{ color: '#749F83' }}, symbol: 'circle', symbolSize: 6 }},
    ]
  }});
}})();

// === Chart 8: 盈利能力 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_profitability'));
  c.setOption({{
    title: {{ text: '盈利能力指标 (%)', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['ROE','费用率','毛利率','净利率','ROA'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '%', max: 60 }},
    series: [
      {{ name: 'ROE', type: 'bar', data: {roe}, itemStyle: {{ color: '#C23531', borderRadius:[4,4,0,0] }} }},
      {{ name: '费用率', type: 'bar', data: {fr}, itemStyle: {{ color: '#91C7AE', borderRadius:[4,4,0,0], opacity: 0.6 }} }},
      {{ name: '毛利率', type: 'line', data: {gm}, lineStyle: {{ color: '#61A0A8', width:2.5 }}, symbol: 'none' }},
      {{ name: '净利率', type: 'line', data: {nm}, lineStyle: {{ color: '#D48265' }}, symbol: 'circle', symbolSize: 7 }},
      {{ name: 'ROA', type: 'line', data: {roa}, lineStyle: {{ color: '#61A0A8', type:'dashed' }}, symbol: 'diamond', symbolSize: 6 }},
    ]
  }});
}})();

// === Chart 9: 成长性 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_growth'));
  c.setOption({{
    title: {{ text: '成长性指标 (%)', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['营收增长率','净利增长率','总资产增长率','净资产增长率'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '%' }},
    series: [
      {{ name: '营收增长率', type: 'bar', data: {rg}, itemStyle: {{
        color: function(p) {{ return p.value >= 0 ? '#C23531' : '#2e7d32'; }},
        borderRadius:[4,4,0,0]
      }}}},
      {{ name: '净利增长率', type: 'bar', data: {pg}, itemStyle: {{
        color: function(p) {{ return p.value >= 0 ? '#E69D87' : '#66bb6a'; }},
        borderRadius:[4,4,0,0], opacity:0.7
      }}}},
      {{ name: '总资产增长率', type: 'line', data: {ag}, lineStyle: {{ color: '#61A0A8' }}, symbol: 'triangle', symbolSize: 8 }},
      {{ name: '净资产增长率', type: 'line', data: {eg}, lineStyle: {{ color: '#91C7AE' }}, symbol: 'diamond', symbolSize: 8 }},
    ]
  }});
}})();

// === Chart 10: 营运能力 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_operation'));
  c.setOption({{
    title: {{ text: '营运能力分析', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['应收周转率','总资产周转率','存货周转率','固资周转率'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: [{{ type: 'value', name: '次' }}, {{ type: 'value', name: '次', min: 0 }}],
    series: [
      {{ name: '应收周转率', type: 'bar', data: {art}, yAxisIndex:0,
        itemStyle: {{ color: '#BDA29A', borderRadius:[4,4,0,0] }} }},
      {{ name: '总资产周转率', type: 'bar', data: {at}, yAxisIndex:0,
        itemStyle: {{ color: '#61A0A8', borderRadius:[4,4,0,0], opacity:.5 }} }},
      {{ name: '存货周转率', type: 'line', data: {invt}, yAxisIndex:1,
        lineStyle: {{ color: '#91C7AE' }}, symbol: 'diamond', symbolSize: 8 }},
      {{ name: '固资周转率', type: 'line', data: {fat}, yAxisIndex:1,
        lineStyle: {{ color: '#C23531' }}, symbol: 'triangle', symbolSize: 8 }},
    ]
  }});
}})();

// === Chart 11: OCF/FCF/CapEx ===
(function(){{
  var c = echarts.init(document.getElementById('ch_ocf'));
  c.setOption({{
    title: {{ text: 'OCF / CapEx / FCF（亿{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['FCF','CapEx','OCF(线)'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '亿{self.currency}' }},
    series: [
      {{ name: 'FCF', type: 'bar', stack: 'ocf', data: {fcf},
        itemStyle: {{ color: '#749F83', borderRadius:[4,4,0,0] }} }},
      {{ name: 'CapEx', type: 'bar', stack: 'ocf', data: {cap},
        itemStyle: {{ color: '#C23531' }} }},
      {{ name: 'OCF(线)', type: 'line', data: {cfo},
        lineStyle: {{ color: '#CA8622', width:2, type:'dashed' }}, symbol: 'none' }},
    ]
  }});
}})();

// === Chart 12: 资产负债比率 ===
(function(){{
  var c = echarts.init(document.getElementById('ch_bs'));
  c.setOption({{
    title: {{ text: '资产负债关键比率 (%)', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['有息负债/总资产','生产资产/总资产','应收/总资产','非主业资产/总资产'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '%' }},
    series: [
      {{ name: '有息负债/总资产', type: 'line', data: {dr},
        lineStyle: {{ color: '#C23531', width:2 }}, symbol: 'circle', symbolSize: 6,
        markLine: {{ silent:true, data:[{{ yAxis:60, lineStyle:{{color:'#C23531',type:'dashed'}}, label:{{formatter:'60%警戒'}} }}] }}
      }},
      {{ name: '生产资产/总资产', type: 'line', data: {pr},
        lineStyle: {{ color: '#C23531' }}, symbol: 'diamond', symbolSize: 6 }},
      {{ name: '应收/总资产', type: 'line', data: {rr},
        lineStyle: {{ color: '#BDA29A' }}, symbol: 'triangle', symbolSize: 6,
        markLine: {{ silent:true, data:[{{ yAxis:30, lineStyle:{{color:'#FF9800',type:'dashed'}}, label:{{formatter:'30%警戒'}} }}] }}
      }},
      {{ name: '非主业资产/总资产', type: 'line', data: {nr},
        lineStyle: {{ color: '#D48265', type:'dashed' }}, symbol: 'none',
        areaStyle: {{ color: 'rgba(212,130,101,.15)' }} }},
    ]
  }});
}})();

// === Chart 13: 净利润 vs OCF ===
(function(){{
  var c = echarts.init(document.getElementById('ch_np_ocf'));
  c.setOption({{
    title: {{ text: '净利润 vs 经营现金流（亿{self.currency}）', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis', formatter: function(ps) {{
      var i = ps[0].dataIndex;
      return ps[0].name + '<br/>净利润: ' + {profit}[i].toFixed(0) + '亿<br/>OCF: ' + {cfo}[i].toFixed(0) + '亿<br/><strong>OCF/NI: ' + {ocf_profit}[i].toFixed(2) + '</strong>';
    }} }},
    legend: {{ data: ['净利润','经营现金流'], bottom: 0 }},
    xAxis: {{ type: 'category', data: {y} }},
    yAxis: {{ type: 'value', name: '亿{self.currency}' }},
    series: [
      {{ name: '净利润', type: 'line', data: {profit},
        lineStyle: {{ color: '#2F4554', width:2.5 }}, symbol: 'circle', symbolSize: 8 }},
      {{ name: '经营现金流', type: 'line', data: {cfo},
        lineStyle: {{ color: '#CA8622', width:2.5 }}, symbol: 'diamond', symbolSize: 8 }},
    ]
  }});
}})();

// === Chart 14: 产品构成 ===
{self._gen_product_chart(product_js)}

}})();
</script>
</body>
</html>'''

    def _gen_product_chart(self, product_js):
        """生成产品构成图表JS"""
        if not self.products or not isinstance(self.products, dict):
            return '// 无产品构成数据'
        
        product_years = sorted(self.products.keys())
        # 收集所有类别
        all_cats = set()
        for y in product_years:
            for k in self.products[y]:
                all_cats.add(k)
        cats = list(all_cats)
        
        # 构建各系列的年份数据
        sd = {}
        for cat in cats:
            sd[cat] = []
        for y in product_years:
            for cat in cats:
                sd[cat].append(self.products[y].get(cat, 0))
        
        # 颜色映射
        color_map = {
            '增值服务': '#C23531', '网络广告': '#61A0A8', '营销服务': '#D48265',
            '金融科技及企业服务': '#91C7AE', '其他': '#6E7074',
        }
        
        series_js = []
        for i, cat in enumerate(cats):
            color = color_map.get(cat, f"hsl({i*60},60%,50%)")
            series_js.append(f"""
      {{ name: {json.dumps(cat)}, type: 'bar', stack: 'total', data: {json.dumps(sd[cat])},
        itemStyle: {{ color: {json.dumps(color)} }} }}""")
        
        py = json.dumps(product_years)
        
        return f"""(function() {{
  var c = echarts.init(document.getElementById('ch_product'));
  c.setOption({{
    title: {{ text: '收入构成演变 (%)', left: 'center', textStyle: {{fontSize:14}} }},
    tooltip: {{ trigger: 'axis', axisPointer: {{type:'shadow'}} }},
    legend: {{ data: {json.dumps(cats)}, bottom: 0 }},
    xAxis: {{ type: 'category', data: {py} }},
    yAxis: {{ type: 'value', name: '%', max: 100 }},
    series: [{','.join(series_js)}]
  }});
}})();"""


# ============================================================
# 第四部分：命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="财报分析报告一键生成器")
    parser.add_argument("--code", required=True, help="股票代码，如 00700 / 600519")
    parser.add_argument("--name", required=True, help="公司名称")
    parser.add_argument("--market", required=True, choices=["hk", "sh", "sz"], help="市场")
    parser.add_argument("--zhsy", help="综合损益表原始输出文件路径（港股用）")
    parser.add_argument("--zcfz", help="资产负债表原始输出文件路径")
    parser.add_argument("--xjll", help="现金流量表原始输出文件路径")
    parser.add_argument("--lrb", help="利润表原始输出文件路径（A股用，替代zhsy）")
    parser.add_argument("--kline", required=True, help="K线数据原始输出文件路径")
    parser.add_argument("--products", help="产品构成JSON文件（可选）")
    parser.add_argument("--output", required=True, help="输出HTML文件路径")
    args = parser.parse_args()
    
    # 根据市场选择表名
    zhsy_file = args.zhsy or args.lrb
    if not zhsy_file or not args.zcfz or not args.xjll:
        print("❌ 需要提供三张表的原始数据文件：--zhsy/--lrb --zcfz --xjll", file=sys.stderr)
        sys.exit(1)
    
    # 解析三表
    print(f"📊 解析 {args.name}({args.code}) 财务数据...")
    income = parse_hk_finance(zhsy_file, "zhsy")
    balance = parse_hk_finance(args.zcfz, "zcfz")
    cashflow = parse_hk_finance(args.xjll, "xjll")
    
    # 确保三表年份对齐
    min_n = min(len(income["years"]), len(balance["years"]), len(cashflow["years"]))
    for key in income:
        if isinstance(income[key], list):
            income[key] = income[key][-min_n:]
    for key in balance:
        if isinstance(balance[key], list):
            balance[key] = balance[key][-min_n:]
    for key in cashflow:
        if isinstance(cashflow[key], list):
            cashflow[key] = cashflow[key][-min_n:]
    
    print(f"  数据覆盖: {income['years'][0]}-{income['years'][-1]} ({min_n}年年报)")
    
    # 解析K线
    stock = parse_kline(args.kline)
    print(f"  K线数据: {stock['years'][0]}-{stock['years'][-1]}")
    
    # 产品构成
    products = None
    if args.products:
        with open(args.products, 'r', encoding='utf-8') as f:
            products = json.load(f)
    
    # 计算指标
    print("🔢 计算衍生指标...")
    ind = calc_indicators(income, balance, cashflow)
    
    # 生成报告
    print("📝 生成HTML报告...")
    gen = ReportGenerator(args.name, args.code, args.market)
    html = gen.build(income, balance, cashflow, ind, stock, products)
    
    # 输出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 报告已生成: {output_path}")
    print(f"   文件大小: {len(html):,} bytes")
    print(f"   图表数量: 14 张 ECharts 交互式图表")
    print(f"   数据年份: {income['years'][0]}-{income['years'][-1]}")
    print(f"\n💡 提示：分析文字部分需 Agent 根据数据补充（模板已自动填充关键数值）")


if __name__ == "__main__":
    main()
