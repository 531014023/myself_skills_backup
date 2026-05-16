#!/usr/bin/env python3
"""
银月红利精选指数 · 综合评分计算器

用法：
  python score_calculator.py --input stocks_data.json
  
输入JSON格式：
  [
    {
      "code": "600519",
      "name": "贵州茅台",
      "dividend_yield": 3.2,        # 股息率(%)
      "roe": 25.5,                    # ROE(%)
      "debt_ratio": 20.0,            # 资产负债率(%)
      "gross_margin": 91.0,          # 毛利率(%)
      "cashflow_ratio": 120.0,       # 经营现金流/净利润(%)
      "dps_history": [19.3, 21.9, 25.6, 30.0, 35.0],  # 近5年每股分红
      "payout_ratio_avg": 45.0,      # 近3年平均股利支付率(%)
      "pe_percentile": 30.0,         # PE历史百分位(%)
      "pb_percentile": 25.0,         # PB历史百分位(%)
      "profit_cagr_3y": 15.0,        # 近3年净利润复合增速(%)
      "revenue_stability": 100,      # 营收稳定性得分(0-100)
      "gross_margin_score": 90,      # 毛利率评分(0-100)
      "industry_rank": 1,            # 行业排名
      "moat_score": 75               # 护城河评分(0-100)
    }
  ]

输出：
  - 各股票综合评分和排名
  - 最终权重分配
  - 组合整体指标
"""

import json
import sys
import argparse


# ============ 评分函数 ============

def score_dividend_yield(yield_pct):
    """股息率评分（权重25%）"""
    if yield_pct >= 8.0:
        return 100
    elif yield_pct >= 6.0:
        return 80
    elif yield_pct >= 5.0:
        return 60
    elif yield_pct >= 4.0:
        return 40
    elif yield_pct >= 3.0:
        return 20
    else:
        return 0


def score_financial_quality(roe, debt_ratio, cashflow_ratio):
    """财务质量评分（权重20%）"""
    # ROE评分（40%）— 匹配framework: >=20%满分, 15-20% 80分, 10-15% 60分
    if roe >= 20:
        roe_score = 100
    elif roe >= 15:
        roe_score = 80
    elif roe >= 10:
        roe_score = 60
    else:
        roe_score = 0
    
    # 负债率评分（30%）— 匹配framework: <20%满分, 20-35% 80分, 35-50% 60分, 50-70% 40分
    if debt_ratio < 20:
        debt_score = 100
    elif debt_ratio < 35:
        debt_score = 80
    elif debt_ratio < 50:
        debt_score = 60
    elif debt_ratio < 70:
        debt_score = 40
    else:
        debt_score = 0
    
    # 现金流评分（30%）
    if cashflow_ratio >= 120:
        cf_score = 100
    elif cashflow_ratio >= 100:
        cf_score = 80
    elif cashflow_ratio >= 80:
        cf_score = 60
    else:
        cf_score = 0
    
    return round(roe_score * 0.4 + debt_score * 0.3 + cf_score * 0.3, 1)


def score_valuation(pe_percentile, pb_percentile):
    """估值评分（权重20%）"""
    def percentile_score(pct):
        if pct < 20:
            return 100
        elif pct < 40:
            return 75
        elif pct < 60:
            return 50
        elif pct < 80:
            return 25
        else:
            return 0
    
    return round(percentile_score(pe_percentile) * 0.5 + percentile_score(pb_percentile) * 0.5, 1)


def score_growth(profit_cagr_3y, revenue_stability):
    """成长评分（权重15%）"""
    # 净利润增速（60%）
    if profit_cagr_3y >= 15:
        cagr_score = 100
    elif profit_cagr_3y >= 8:
        cagr_score = 75
    elif profit_cagr_3y >= 0:
        cagr_score = 50
    else:
        cagr_score = 0
    
    return round(cagr_score * 0.6 + revenue_stability * 0.4, 1)


def score_competitiveness(gross_margin, industry_rank, moat_score):
    """竞争力评分（权重15%）"""
    # 毛利率评分（40%）— 匹配framework: >=60%满分, 40-60% 75分, 20-40% 50分
    if gross_margin >= 60:
        gm_score = 100
    elif gross_margin >= 40:
        gm_score = 75
    elif gross_margin >= 20:
        gm_score = 50
    else:
        gm_score = 0
    
    # 行业排名（30%）
    if industry_rank == 1:
        rank_score = 100
    elif industry_rank <= 3:
        rank_score = 70
    else:
        rank_score = 40
    
    return round(gm_score * 0.4 + rank_score * 0.3 + moat_score * 0.3, 1)


def calc_total_score(stock):
    """计算综合评分"""
    score_yield = score_dividend_yield(stock['dividend_yield'])
    score_finance = score_financial_quality(
        stock['roe'], stock['debt_ratio'], stock['cashflow_ratio']
    )
    score_val = score_valuation(stock['pe_percentile'], stock['pb_percentile'])
    score_grow = score_growth(stock['profit_cagr_3y'], stock['revenue_stability'])
    score_comp = score_competitiveness(
        stock['gross_margin'], stock['industry_rank'], stock['moat_score']
    )
    
    total = (
        score_yield * 0.25 +
        score_finance * 0.20 +
        score_val * 0.25 +
        score_grow * 0.15 +
        score_comp * 0.15
    )
    
    return {
        'score_yield': score_yield,
        'score_finance': score_finance,
        'score_valuation': score_val,
        'score_growth': score_grow,
        'score_competitiveness': score_comp,
        'total_score': round(total, 1)
    }


def check_veto_conditions(stock):
    """检查一票否决条件"""
    reasons = []
    
    # 分红稳定性 - 方案A：单年下降不超过20%
    if 'dps_history' in stock and len(stock['dps_history']) >= 2:
        for i in range(1, len(stock['dps_history'])):
            prev = stock['dps_history'][i - 1]
            curr = stock['dps_history'][i]
            if prev > 0:
                decline = (curr - prev) / prev
                if decline < -0.20:
                    reasons.append(f"分红下降超过20%（第{i}年到第{i+1}年下降{abs(decline)*100:.1f}%）")
    
    # 股利支付率范围（仅上限≤100%）
    if 'payout_ratio_avg' in stock:
        pr = stock['payout_ratio_avg']
        if pr > 100:
            reasons.append(f"股利支付率{pr:.1f}% > 100%，分红不可持续")
    
    return reasons


def allocate_weights(stocks_with_scores, single_stock_limit=5.0, single_industry_limit=20.0):
    """
    股息率加权 + 比例压缩法约束调整（匹配framework）
    
    参数:
        stocks_with_scores: 带有评分和计算权重的股票列表
        single_stock_limit: 单只上限%
        single_industry_limit: 单行业上限%
    
    返回:
        带有最终权重的股票列表
    """
    # 初始权重 = 个股股息率 / 总股息率
    total_dividend_yield = sum(s['dividend_yield'] for s in stocks_with_scores)
    
    for s in stocks_with_scores:
        s['raw_weight'] = round((s['dividend_yield'] / total_dividend_yield) * 100, 2)
        s['weight'] = s['raw_weight']
    
    # 比例压缩法（不是再分配法）：所有权重乘以相同压缩因子
    max_w = max(s['weight'] for s in stocks_with_scores)
    if max_w > single_stock_limit:
        factor = single_stock_limit / max_w
        for s in stocks_with_scores:
            s['weight'] = round(s['weight'] * factor, 2)
    
    # 单行业上限约束
    max_iterations = 10
    for _ in range(max_iterations):
        changed = False
        industries = {}
        for s in stocks_with_scores:
            ind = s.get('industry', '其他')
            if ind not in industries:
                industries[ind] = []
            industries[ind].append(s)
        
        for ind, stocks in industries.items():
            total_ind_weight = sum(s['weight'] for s in stocks)
            if total_ind_weight > single_industry_limit:
                ratio = single_industry_limit / total_ind_weight
                for s in stocks:
                    s['weight'] = round(s['weight'] * ratio, 2)
                changed = True
        
        if not changed:
            break
    
    # 不归一化！压缩后总和<100%即为现金储备
    return stocks_with_scores


def analyze_portfolio(stocks_with_scores):
    """分析组合整体指标"""
    total_weight = sum(s['weight'] for s in stocks_with_scores)
    
    # 加权股息率
    weighted_yield = sum(s['dividend_yield'] * s['weight'] for s in stocks_with_scores) / total_weight
    
    # 加权ROE
    weighted_roe = sum(s['roe'] * s['weight'] for s in stocks_with_scores) / total_weight
    
    # 加权负债率
    weighted_debt = sum(s['debt_ratio'] * s['weight'] for s in stocks_with_scores) / total_weight
    
    # 行业分布
    industry_dist = {}
    for s in stocks_with_scores:
        ind = s.get('industry', '其他')
        industry_dist[ind] = industry_dist.get(ind, 0) + s['weight']
    
    return {
        'total_stocks': len(stocks_with_scores),
        'combined_dividend_yield': round(weighted_yield, 2),
        'combined_roe': round(weighted_roe, 2),
        'combined_debt_ratio': round(weighted_debt, 2),
        'industry_distribution': {k: round(v, 1) for k, v in sorted(industry_dist.items(), key=lambda x: -x[1])}
    }


def main():
    parser = argparse.ArgumentParser(description='银月红利精选指数 · 综合评分计算')
    parser.add_argument('--input', '-i', required=True, help='输入JSON文件路径')
    parser.add_argument('--output', '-o', help='输出JSON文件路径（可选）')
    parser.add_argument('--top', '-t', type=int, default=30, help='选取TOP N只（默认30）')
    args = parser.parse_args()
    
    with open(args.input, 'r', encoding='utf-8') as f:
        stocks = json.load(f)
    
    print(f"读取 {len(stocks)} 只股票数据")
    print("=" * 60)
    
    # 筛选：一票否决检查
    passed = []
    vetoed = []
    for s in stocks:
        reasons = check_veto_conditions(s)
        if reasons:
            vetoed.append((s, reasons))
        else:
            passed.append(s)
    
    if vetoed:
        print(f"\n🛑 一票否决剔除 {len(vetoed)} 只:")
        for s, reasons in vetoed:
            print(f"  - {s.get('name', s.get('code', '未知'))}: {'; '.join(reasons)}")
    
    print(f"\n通过筛选: {len(passed)} 只")
    
    # 计算评分
    results = []
    for s in passed:
        scores = calc_total_score(s)
        results.append({**s, **scores})
    
    # 按总分排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 取TOP
    top_n = min(args.top, len(results))
    top_results = results[:top_n]
    
    print(f"\n{'=' * 60}")
    print(f"📊 TOP {top_n} 评分排名")
    print(f"{'=' * 60}")
    print(f"{'排名':<4} {'名称':<12} {'总分':<6} {'股息':<6} {'财务':<6} {'估值':<6} {'成长':<6} {'竞争':<6} {'股息率%':<8}")
    print("-" * 60)
    
    for i, s in enumerate(top_results, 1):
        print(
            f"{i:<4} {s.get('name', s.get('code', ''))[:8]:<12} "
            f"{s['total_score']:<6} {s['score_yield']:<6} "
            f"{s['score_finance']:<6} {s['score_valuation']:<6} "
            f"{s['score_growth']:<6} {s['score_competitiveness']:<6} "
            f"{s['dividend_yield']:<8}"
        )
    
    # 权重分配
    weighted = allocate_weights(top_results)
    
    print(f"\n{'=' * 60}")
    print(f"⚖️ 股息率加权仓位分配")
    print(f"{'=' * 60}")
    print(f"{'排名':<4} {'名称':<12} {'股息率%':<8} {'原始权重%':<10} {'最终权重%':<10}")
    print("-" * 60)
    
    for i, s in enumerate(weighted, 1):
        print(
            f"{i:<4} {s.get('name', s.get('code', ''))[:8]:<12} "
            f"{s['dividend_yield']:<8} {s['raw_weight']:<10} {s['weight']:<10}"
        )
    
    # 组合分析
    analysis = analyze_portfolio(weighted)
    
    print(f"\n{'=' * 60}")
    print(f"📈 组合整体指标")
    print(f"{'=' * 60}")
    print(f"持仓数量: {analysis['total_stocks']} 只")
    print(f"组合加权股息率: {analysis['combined_dividend_yield']}%")
    print(f"组合加权ROE: {analysis['combined_roe']}%")
    print(f"组合加权负债率: {analysis['combined_debt_ratio']}%")
    print(f"\n行业分布:")
    for ind, weight in analysis['industry_distribution'].items():
        bar = "█" * int(weight / 2)
        print(f"  {ind:<12} {weight:>5.1f}% {bar}")
    
    # 输出
    if args.output:
        output = {
            'summary': analysis,
            'stocks': [
                {
                    'name': s.get('name'),
                    'code': s.get('code'),
                    'industry': s.get('industry'),
                    'dividend_yield': s['dividend_yield'],
                    'total_score': s['total_score'],
                    'weight': s['weight'],
                    'scores': {
                        'dividend': s['score_yield'],
                        'financial_quality': s['score_finance'],
                        'valuation': s['score_valuation'],
                        'growth': s['score_growth'],
                        'competitiveness': s['score_competitiveness']
                    }
                }
                for s in weighted
            ],
            'vetoed': [
                {'name': s.get('name'), 'reasons': reasons}
                for s, reasons in vetoed
            ]
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 完整结果已保存到 {args.output}")


if __name__ == '__main__':
    main()
