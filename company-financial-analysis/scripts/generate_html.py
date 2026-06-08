#!/usr/bin/env python3
"""
企业财务分析 - HTML报告生成器
基于 ECharts 5 生成交互式财务分析报告。

用法:
    python generate_html.py --data data.json --output 公司研究/贵州茅台/贵州茅台_企业分析_2026-06-04.html
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime


# ============================================================
# HTML 模板
# ============================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} 企业财务深度分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", sans-serif; background: #f5f7fa; color: #333; }}
.report-header {{
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white; padding: 40px; text-align: center;
}}
.report-header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.report-header .meta {{ font-size: 14px; opacity: 0.8; }}
.report-header .meta span {{ margin: 0 12px; }}
.layout {{ display: flex; min-height: 100vh; }}
.sidebar {{
  width: 260px; min-width: 260px; background: #fff;
  border-right: 1px solid #e8e8e8; padding: 20px 0;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
}}
.sidebar h3 {{ font-size: 14px; color: #999; padding: 8px 24px; text-transform: uppercase; letter-spacing: 1px; }}
.sidebar a {{
  display: block; padding: 8px 24px; color: #555; text-decoration: none;
  font-size: 13px; border-left: 3px solid transparent; transition: all 0.2s;
}}
.sidebar a:hover, .sidebar a.active {{ color: #C23531; background: #fef0f0; border-left-color: #C23531; }}
.content {{ flex: 1; padding: 24px 32px; max-width: 1200px; }}
.section {{
  background: #fff; border-radius: 12px; padding: 28px; margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
.section h2 {{
  font-size: 20px; color: #1a1a2e; margin-bottom: 8px;
  padding-bottom: 12px; border-bottom: 2px solid #C23531;
}}
.section h3 {{ font-size: 16px; color: #444; margin: 20px 0 12px; }}
.section h4 {{ font-size: 14px; color: #666; margin: 16px 0 8px; }}
.chart-container {{ width: 100%; height: 400px; margin: 16px 0; }}
.chart-container.small {{ height: 350px; }}
.chart-container.large {{ height: 500px; }}
.analysis-text {{ 
  font-size: 14px; line-height: 1.8; color: #555;
  background: #fafafa; padding: 16px 20px; border-radius: 8px;
  margin: 12px 0; border-left: 4px solid #C23531;
}}
.alert {{ background: #fff3e0; border-left-color: #ff9800; }}
.alert-danger {{ background: #ffebee; border-left-color: #f44336; }}
.alert-good {{ background: #e8f5e9; border-left-color: #4caf50; }}
.tag {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; margin: 2px; }}
.tag-red {{ background: #ffebee; color: #c62828; }}
.tag-green {{ background: #e8f5e9; color: #2e7d32; }}
.tag-orange {{ background: #fff3e0; color: #e65100; }}
.tag-blue {{ background: #e3f2fd; color: #1565c0; }}
.tag-gray {{ background: #f5f5f5; color: #616161; }}
.cf-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
.cf-table th {{ background: #f5f5f5; padding: 10px 12px; text-align: center; border: 1px solid #e0e0e0; }}
.cf-table td {{ padding: 8px 12px; text-align: center; border: 1px solid #e0e0e0; }}
.cf-positive {{ background: #e8f5e9; color: #2e7d32; font-weight: bold; }}
.cf-negative {{ background: #ffebee; color: #c62828; font-weight: bold; }}
.conclusion-card {{
  background: linear-gradient(135deg, #fff 0%, #fef0f0 100%);
  border: 1px solid #fcd4d4; border-radius: 12px; padding: 24px;
  margin-bottom: 16px;
}}
.conclusion-card h3 {{ color: #C23531; margin-bottom: 12px; }}
.conclusion-card ul {{ padding-left: 20px; }}
.conclusion-card li {{ font-size: 14px; line-height: 2; color: #555; }}
.checklist {{ font-size: 13px; }}
.checklist .item {{ display: flex; align-items: center; padding: 6px 0; border-bottom: 1px solid #f0f0f0; }}
.checklist .item .status {{ width: 24px; text-align: center; margin-right: 8px; }}
.checklist .item .label {{ flex: 1; }}
.checklist .item .result {{ font-weight: bold; margin-right: 8px; }}
.rating-box {{
  display: inline-block; padding: 8px 24px; border-radius: 24px;
  font-size: 18px; font-weight: bold; margin: 12px 0;
}}
.rating-safe {{ background: #e8f5e9; color: #2e7d32; }}
.rating-watch {{ background: #fff8e1; color: #f57f17; }}
.rating-alert {{ background: #fff3e0; color: #e65100; }}
.rating-danger {{ background: #ffebee; color: #c62828; }}
.summary-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px; margin: 16px 0;
}}
.summary-card {{
  background: #fff; border-radius: 10px; padding: 20px;
  text-align: center; box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}}
.summary-card .value {{ font-size: 28px; font-weight: bold; color: #C23531; }}
.summary-card .label {{ font-size: 12px; color: #999; margin-top: 4px; }}
@media print {{
  .sidebar {{ display: none; }}
  .content {{ padding: 0; }}
  .section {{ box-shadow: none; break-inside: avoid; }}
}}
</style>
</head>
<body>

<div class="report-header">
  <h1>{company_name} ({stock_code})</h1>
  <div class="meta">
    <span>📅 分析日期: {analysis_date}</span>
    <span>📊 数据覆盖: {data_range}</span>
    <span>🏭 行业: {industry}</span>
    <span>📈 上市日期: {ipo_date}</span>
  </div>
</div>

<div class="layout">
  <nav class="sidebar" id="sidebar">
    <h3>第一轮 · 鸟瞰</h3>
    <a href="#s1-company">1.1 公司基本信息</a>
    <a href="#s1-price">1.2 股价历史</a>
    <a href="#s1-revenue">1.3 营收历史</a>
    <a href="#s1-profit">1.4 净利润历史</a>
    
    <h3>第二轮 · 结构</h3>
    <a href="#s2-roe">2.1 ROE深度分析</a>
    <a href="#s2-assets">2.2 资产结构</a>
    <a href="#s2-cf-portrait">2.3 现金流肖像</a>
    <a href="#s2-cf-np">2.4 现金流 vs 净利润</a>
    <a href="#s2-cash-rev">2.5 收现 vs 营收</a>
    
    <h3>第三轮 · 排雷</h3>
    <a href="#s3-anomaly">3.1 科目异常检查</a>
    <a href="#s3-bs-history">3.2 资产负债历史</a>
    <a href="#s3-is-history">3.3 利润表历史</a>
    <a href="#s3-cf-history">3.4 现金流历史</a>
    <a href="#s3-ratios">3.5 财务指标</a>
    <a href="#s3-peers">3.6 同行对比</a>
    
    <h3>第四轮 · 综合</h3>
    <a href="#s4-summary">4.1 财务画像总结</a>
    
    <h3>第五轮 · 结论</h3>
    <a href="#s5-conclusion">5.1 结论与建议</a>
  </nav>
  
  <main class="content" id="content">
    {sections}
  </main>
</div>

<script>
// ECharts 通用配置
const COLORS = {{
  revenue: '#C23531', netProfit: '#2F4554', stockPrice: '#C23531',
  grossMargin: '#61A0A8', netMargin: '#D48265', feeRate: '#91C7AE',
  cashFlow: '#CA8622', salesCash: '#BDA29A', liabilities: '#6E7074',
  cashBalance: '#749F83', investOut: '#C23531', dividend: '#546570',
  roe: '#C23531', asset: '#61A0A8', equity: '#91C7AE',
  prodAsset: '#C23531', bizAsset: '#61A0A8', investAsset: '#D48265',
  company: '#C23531', peer1: '#61A0A8', peer2: '#D48265',
  peer3: '#91C7AE', peer4: '#CA8622', industry: '#6E7074'
}};

function initChart(domId, option) {{
  const dom = document.getElementById(domId);
  if (!dom) return;
  // Ensure container has correct height
  if (dom.clientHeight === 0) {{
    const cls = dom.className || '';
    if (cls.includes('large')) dom.style.height = '500px';
    else if (cls.includes('small')) dom.style.height = '350px';
    else dom.style.height = '400px';
  }}
  const chart = echarts.init(dom);
  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
  return chart;
}}

// 通用折线图选项生成
function lineChart(title, xData, series, yName, extra = {{}}) {{
  return {{
    title: {{ text: title, left: 'center', textStyle: {{ fontSize: 16, color: '#333' }} }},
    tooltip: {{ trigger: 'axis' }},
    legend: extra.legend || {{ bottom: 0 }},
    grid: {{ left: '3%', right: '4%', bottom: extra.bottom || '15%', containLabel: true }},
    xAxis: {{ type: 'category', data: xData, axisLabel: {{ rotate: extra.rotate || 0 }} }},
    yAxis: {{ type: 'value', name: yName }},
    series: series,
    ...(extra.overrides || {{}})
  }};
}}

// 通用柱状图
function barChart(title, xData, data, yName, color, extra = {{}}) {{
  return lineChart(title, xData, [{{
    type: 'bar', data: data, itemStyle: {{ color: color or COLORS.revenue }},
    label: extra.showLabel ? {{ show: true, position: 'top', fontSize: 10 }} : {{}},
  }}], yName, extra);
}}

// 通用饼图
function pieChart(title, data, extra = {{}}) {{
  return {{
    title: {{ text: title, left: 'center', textStyle: {{ fontSize: 16 }} }},
    tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}} ({{d}}%)' }},
    legend: {{ orient: 'vertical', left: 'left', top: 'middle' }},
    series: [{{
      type: 'pie', radius: extra.radius || ['40%', '70%'],
      center: ['55%', '50%'],
      data: data,
      label: {{ formatter: '{{b}}\\n{{d}}%' }},
      emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }} }}
    }}]
  }};
}}

// 组合图 (双Y轴)
function comboChart(title, xData, barSeries, lineSeries, leftName, rightName) {{
  return {{
    title: {{ text: title, left: 'center', textStyle: {{ fontSize: 16, color: '#333' }} }},
    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
    legend: {{ bottom: 0 }},
    grid: {{ left: '3%', right: '4%', bottom: '15%', containLabel: true }},
    xAxis: {{ type: 'category', data: xData }},
    yAxis: [
      {{ type: 'value', name: leftName, position: 'left' }},
      {{ type: 'value', name: rightName, position: 'right' }}
    ],
    series: [
      ...barSeries.map(s => ({{ ...s, yAxisIndex: 0 }})),
      ...lineSeries.map(s => ({{ ...s, yAxisIndex: 1, type: 'line' }}))
    ]
  }};
}}

// 初始化所有图表
document.addEventListener('DOMContentLoaded', function() {{
  {chart_inits}
}});
</script>
</body>
</html>'''


# ============================================================
# 图表配置生成函数
# ============================================================

def gen_price_chart(data):
    """图1: 股价历史走势"""
    p = data["processed"]["income"]
    prices = p.get("stock_prices", [])
    years = p.get("price_years", []) or p["years"]
    if not prices:
        return None
    
    cagr = p.get("price_cagr")
    cagr_text = f"年化增长: {cagr:.2f}%" if cagr else ""
    
    return {
        "title": f"股价历史走势 {cagr_text}",
        "type": "line",
        "option": json.dumps({
            "title": {"text": f"股价历史走势（前复权）", "subtext": cagr_text, "left": "center"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": years},
            "yAxis": {"type": "value", "name": "股价(元)"},
            "series": [{
                "type": "line", "data": prices,
                "itemStyle": {"color": COLORS_STOCK},
                "areaStyle": {"color": "rgba(194,53,49,0.1)"},
                "smooth": True
            }]
        }, ensure_ascii=False)
    }


def gen_revenue_chart(data):
    """图2: 营收历史"""
    p = data["processed"]["income"]
    return {
        "title": f"营业收入历史 (年化增长: {p.get('revenue_cagr', 'N/A'):.2f}%",
        "type": "bar",
        "option": json.dumps({
            "title": {"text": "营业收入历史", "subtext": f"年化增长: {p.get('revenue_cagr', 0):.2f}%", "left": "center"},
            "tooltip": {"trigger": "axis", "formatter": "{b}年: {c}亿元"},
            "xAxis": {"type": "category", "data": p["years"]},
            "yAxis": {"type": "value", "name": "营收(亿元)"},
            "series": [{
                "type": "bar", "data": p["revenue"],
                "itemStyle": {"color": COLORS_REV},
                "label": {"show": True, "position": "top", "fontSize": 10, "formatter": "{c}"}
            }]
        }, ensure_ascii=False)
    }


def gen_profit_chart(data):
    """图3: 净利润历史"""
    p = data["processed"]["income"]
    return {
        "title": f"归母净利润历史 (年化增长: {p.get('net_profit_cagr', 0):.2f}%",
        "type": "bar",
        "option": json.dumps({
            "title": {"text": "归母净利润历史", "subtext": f"年化增长: {p.get('net_profit_cagr', 0):.2f}%", "left": "center"},
            "tooltip": {"trigger": "axis", "formatter": "{b}年: {c}亿元"},
            "xAxis": {"type": "category", "data": p["years"]},
            "yAxis": {"type": "value", "name": "净利润(亿元)"},
            "series": [{
                "type": "bar", "data": p["net_profit"],
                "itemStyle": {"color": COLORS_NP}
            }]
        }, ensure_ascii=False)
    }


def gen_roe_chart(data):
    """图4: ROE深度分析 - 多面板"""
    p = data["processed"]["income"]
    roe = data["processed"]["roe"]
    
    return {
        "title": "ROE深度拆解（杜邦分析 + 五层穿透）",
        "type": "multi",
        "option": json.dumps({
            "title": {"text": "ROE深度拆解", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"bottom": 0},
            "grid": {"left": "3%", "right": "4%", "bottom": "18%", "containLabel": True},
            "xAxis": {"type": "category", "data": p["years"]},
            "yAxis": {"type": "value", "name": "%"},
            "series": [
                {"name": "ROE", "type": "line", "data": roe["roe"], "lineStyle": {"width": 3}, "itemStyle": {"color": COLORS_ROE}},
                {"name": "ROA", "type": "line", "data": roe["roa"], "itemStyle": {"color": COLORS_ASSET}},
                {"name": "营业利润率", "type": "line", "data": p["operating_margin"], "itemStyle": {"color": "#E69D87"}},
                {"name": "净利率", "type": "line", "data": p["net_margin"], "itemStyle": {"color": COLORS_NM}},
                {"name": "毛利率", "type": "line", "data": p["gross_margin"], "itemStyle": {"color": COLORS_GM}},
            ]
        }, ensure_ascii=False)
    }


def gen_asset_pie(data):
    """图5: 资产结构饼图"""
    struct = data["processed"]["income"].get("latest_asset_structure", {})
    if not struct:
        return None
    
    pie_data = [
        {"value": struct.get("生产资产", 0), "name": "生产资产", "itemStyle": {"color": COLORS_PA}},
        {"value": struct.get("经营资产", 0), "name": "经营资产", "itemStyle": {"color": COLORS_BA}},
        {"value": struct.get("投资资产", 0), "name": "投资资产", "itemStyle": {"color": COLORS_IA}},
    ]
    
    return {
        "title": "资产结构分布",
        "type": "pie",
        "option": json.dumps({
            "title": {"text": "资产结构分布（最新一期）", "left": "center"},
            "tooltip": {"trigger": "item", "formatter": "{b}: {c}亿元 ({d}%)"},
            "legend": {"bottom": 0},
            "series": [{
                "type": "pie", "radius": ["40%", "70%"], "center": ["50%", "45%"],
                "data": pie_data,
                "label": {"formatter": "{b}\n{d}%"},
                "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"}}
            }]
        }, ensure_ascii=False)
    }


def gen_cf_portrait(data):
    """现金流肖像表格 - 返回HTML表格"""
    cf = data["processed"]["cashflow"]
    years = data["processed"]["income"]["years"]
    
    rows = ""
    type_names = {
        "+++": "妖精型", "++-": "老母鸡型", "+-+": "蛮牛型", "+--": "奶牛型",
        "---": "大出血型", "--+": "赌徒型", "-+-": "混吃等死型", "-++": "骗吃骗喝型",
    }
    
    for i, year in enumerate(years):
        if i < len(cf["cf_portrait"]):
            p = cf["cf_portrait"][i]
            key = "".join(p)
            typename = type_names.get(key, "未知")
            ops = p[0]; inv = p[1]; fin = p[2]
            rows += f'''<tr>
                <td>{year}</td>
                <td class="{'cf-positive' if ops=='+' else 'cf-negative'}">{"+流入" if ops=='+' else "-流出"}</td>
                <td class="{'cf-positive' if inv=='+' else 'cf-negative'}">{"+流入" if inv=='+' else "-流出"}</td>
                <td class="{'cf-positive' if fin=='+' else 'cf-negative'}">{"+流入" if fin=='+' else "-流出"}</td>
                <td><strong>{typename}</strong></td>
            </tr>'''
    
    return f'''<table class="cf-table">
        <thead><tr><th>年份</th><th>经营活动</th><th>投资活动</th><th>筹资活动</th><th>肖像类型</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>'''


def gen_ocf_np_chart(data):
    """图14: 净利润 vs 经营现金流"""
    p = data["processed"]["income"]
    cf = data["processed"]["cashflow"]
    
    return {
        "title": "净利润 vs 经营现金流净额",
        "type": "line",
        "option": json.dumps({
            "title": {"text": "净利润 vs 经营现金流净额", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"bottom": 0},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": p["years"]},
            "yAxis": {"type": "value", "name": "金额(亿元)"},
            "series": [
                {"name": "归母净利润", "type": "line", "data": p["net_profit"], "itemStyle": {"color": COLORS_NP}},
                {"name": "经营现金流净额", "type": "line", "data": cf["operating_cf"], "itemStyle": {"color": COLORS_CF}},
            ]
        }, ensure_ascii=False)
    }


def gen_sales_cash_chart(data):
    """图15: 销售收现 vs 营收"""
    p = data["processed"]["income"]
    cf = data["processed"]["cashflow"]
    
    return {
        "title": "销售收现 vs 营业收入",
        "type": "line",
        "option": json.dumps({
            "title": {"text": "销售收现 vs 营业收入", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"bottom": 0},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": p["years"]},
            "yAxis": {"type": "value", "name": "金额(亿元)"},
            "series": [
                {"name": "营业收入", "type": "line", "data": p["revenue"], "itemStyle": {"color": COLORS_REV}},
                {"name": "销售收现", "type": "line", "data": cf["sales_cash"], "itemStyle": {"color": COLORS_SC}},
            ]
        }, ensure_ascii=False)
    }


# ============================================================
# 颜色常量 (用于JSON序列化)
# ============================================================
COLORS_REV = "#C23531"
COLORS_NP = "#2F4554"
COLORS_ROE = "#C23531"
COLORS_ASSET = "#61A0A8"
COLORS_NM = "#D48265"
COLORS_GM = "#61A0A8"
COLORS_CF = "#CA8622"
COLORS_SC = "#BDA29A"
COLORS_STOCK = "#C23531"
COLORS_PA = "#C23531"
COLORS_BA = "#61A0A8"
COLORS_IA = "#D48265"


# ============================================================
# 生成完整报告
# ============================================================

def generate_report(data, output_path):
    """生成完整的HTML分析报告"""
    
    meta = data["meta"]
    proc = data["processed"]
    inc = proc["income"]
    bal = proc["balance"]
    cf = proc["cashflow"]
    
    # 构建各section
    sections = []
    chart_inits = []
    chart_id = 0
    
    def add_chart(gen_func):
        nonlocal chart_id, chart_inits
        result = gen_func(data)
        if result is None:
            return ""
        chart_id += 1
        cid = f"chart{chart_id}"
        if result["type"] in ("line", "bar", "pie", "multi"):
            chart_inits.append(f"initChart('{cid}', {result['option']});")
            h = "large" if result["type"] == "multi" else ""
            return f'''
            <h4>{result["title"]}</h4>
            <div class="chart-container {h}" id="{cid}"></div>'''
        else:
            return result.get("html", "")
    
    # ---- 第一轮：鸟瞰 ----
    sections.append(f'''<div class="section" id="s1-company">
        <h2>1.1 公司基本信息</h2>
        <div class="summary-grid">
            <div class="summary-card"><div class="value">{meta['name']}</div><div class="label">公司名称</div></div>
            <div class="summary-card"><div class="value">{meta['code']}</div><div class="label">股票代码</div></div>
            <div class="summary-card"><div class="value">{meta.get('industry', 'N/A')}</div><div class="label">所属行业</div></div>
            <div class="summary-card"><div class="value">{meta.get('ipo_date', 'N/A')}</div><div class="label">上市日期</div></div>
        </div>
    </div>''')
    
    sections.append(f'<div class="section" id="s1-price"><h2>1.2 股价历史走势</h2>{add_chart(gen_price_chart)}</div>')
    sections.append(f'<div class="section" id="s1-revenue"><h2>1.3 营业收入历史</h2>{add_chart(gen_revenue_chart)}</div>')
    sections.append(f'<div class="section" id="s1-profit"><h2>1.4 归母净利润历史</h2>{add_chart(gen_profit_chart)}</div>')
    
    # ---- 第二轮：结构 ----
    roe_chart = add_chart(gen_roe_chart)
    sections.append(f'<div class="section" id="s2-roe"><h2>2.1 ROE深度分析</h2>{roe_chart}</div>')
    sections.append(f'<div class="section" id="s2-assets"><h2>2.2 资产结构分布</h2>{add_chart(gen_asset_pie)}</div>')
    
    cf_table = gen_cf_portrait(data)
    sections.append(f'<div class="section" id="s2-cf-portrait"><h2>2.3 现金流肖像</h2>{cf_table}</div>')
    sections.append(f'<div class="section" id="s2-cf-np"><h2>2.4 现金流 vs 净利润</h2>{add_chart(gen_ocf_np_chart)}</div>')
    sections.append(f'<div class="section" id="s2-cash-rev"><h2>2.5 收现 vs 营收</h2>{add_chart(gen_sales_cash_chart)}</div>')
    
    # ---- 第三轮：排雷占位 ----
    for sec_id, sec_title in [
        ("s3-anomaly", "3.1 科目异常检查"),
        ("s3-bs-history", "3.2 资产负债表历史分析"),
        ("s3-is-history", "3.3 利润表历史分析"),
        ("s3-cf-history", "3.4 现金流量表历史分析"),
        ("s3-ratios", "3.5 财务指标分析"),
        ("s3-peers", "3.6 同行对比"),
    ]:
        sections.append(f'<div class="section" id="{sec_id}"><h2>{sec_title}</h2><p style="color:#999">此部分由 AI Agent 在分析过程中动态生成详细图表和内容。</p></div>')
    
    # ---- 第四轮 + 第五轮 ----
    sections.append(f'''<div class="section" id="s4-summary">
        <h2>4.1 财务画像总结</h2>
        <p style="color:#999">此部分由 AI Agent 在分析过程中根据前三轮结果综合生成。</p>
    </div>''')
    
    sections.append(f'''<div class="section" id="s5-conclusion">
        <h2>5.1 结论与建议</h2>
        <p style="color:#999">此部分由 AI Agent 在分析过程中生成最终结论。</p>
    </div>''')
    
    # 组装HTML
    html = HTML_TEMPLATE.format(
        company_name=meta["name"],
        stock_code=meta["code"],
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        data_range=f'{inc["years"][0]} - {inc["years"][-1]}',
        industry=meta.get("industry", "N/A"),
        ipo_date=meta.get("ipo_date", "N/A"),
        sections="\n".join(sections),
        chart_inits="\n  ".join(chart_inits) if chart_inits else "// 暂无图表数据",
    )
    
    # 写入文件
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="企业财务分析HTML报告生成器")
    parser.add_argument("--data", required=True, help="fetch_data.py输出的JSON数据文件")
    parser.add_argument("--output", required=True, help="输出HTML文件路径")
    parser.add_argument("--company-dir", help="公司研究目录路径 (可选，自动推断)")
    args = parser.parse_args()
    
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    result_path = generate_report(data, args.output)
    print(f"✅ 报告已生成: {result_path}")


if __name__ == "__main__":
    main()
