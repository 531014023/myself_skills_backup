#!/usr/bin/env python3
"""
企业财务分析 - 数据获取与结构化处理
将从 mx-data / tdx-connector 获取的原始数据加工为图表所需的标准化JSON格式。

用法：
    python fetch_data.py --code 600519 --market SH --output data.json
    或从标准输入读取原始数据：
    cat raw_data.txt | python fetch_data.py --code 600519 --output data.json

数据获取由 AI Agent 通过 mx-data skill 完成，本脚本负责数据校验、计算和结构化。
"""

import json
import sys
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="企业财务数据标准化处理")
    parser.add_argument("--code", required=True, help="股票代码")
    parser.add_argument("--name", default="", help="公司名称")
    parser.add_argument("--market", default="SH", help="市场 (SH/SZ/HK/US)")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--raw", help="原始数据JSON文件路径")
    return parser.parse_args()


def calc_cagr(start_val, end_val, years):
    """计算年化复合增长率"""
    if start_val <= 0 or end_val <= 0 or years <= 0:
        return None
    return (pow(end_val / start_val, 1 / years) - 1) * 100


def process_financial_data(raw_data, code, name):
    """
    将原始财务数据处理为标准化结构
    
    raw_data 应包含：
    {
        "company": { "name": "", "code": "", "market": "", "industry": "", "ipo_date": "" },
        "stock_price": [{"year": 2001, "close": 35.5}, ...],
        "income": [
            {
                "year": 2020,
                "revenue": 100.0,           # 营业总收入 (亿元)
                "operating_revenue": 95.0,  # 营业收入 (亿元)
                "operating_cost": 30.0,     # 营业成本
                "gross_profit": 65.0,       # 毛利
                "sell_expense": 10.0,       # 销售费用
                "admin_expense": 5.0,       # 管理费用
                "finance_expense": -2.0,    # 财务费用 (负=净收入)
                "rd_expense": 3.0,          # 研发费用
                "asset_impairment": 0.5,    # 资产减值损失
                "fair_value_change": 0.2,   # 公允价值变动收益
                "invest_income": 1.0,       # 投资收益
                "operating_profit": 50.0,   # 营业利润
                "total_profit": 50.0,       # 利润总额
                "income_tax": 12.5,         # 所得税费用
                "net_profit": 37.5,         # 净利润
                "parent_net_profit": 35.0,  # 归母净利润
                "minority_interest": 2.5,   # 少数股东损益
            }, ...
        ],
        "balance": [
            {
                "year": 2020,
                "total_assets": 500.0,
                "current_assets": 300.0,
                "cash": 100.0,              # 货币资金
                "notes_receivable": 5.0,    # 应收票据
                "accounts_receivable": 10.0,# 应收账款
                "prepayments": 5.0,         # 预付账款
                "other_receivables": 2.0,   # 其他应收款
                "inventory": 50.0,          # 存货
                "fixed_assets": 80.0,       # 固定资产
                "construction": 20.0,       # 在建工程
                "right_of_use": 10.0,       # 使用权资产
                "intangible_assets": 15.0,  # 无形资产
                "goodwill": 5.0,            # 商誉
                "lt_equity_invest": 10.0,   # 长期股权投资
                "trading_financial": 2.0,   # 交易性金融资产
                "other_financial": 3.0,     # 其他权益/债权投资
                "invest_real_estate": 0.0,  # 投资性房地产
                "long_term_prepaid": 1.0,   # 长期待摊费用
                "total_liabilities": 200.0,
                "current_liabilities": 150.0,
                "short_borrowing": 20.0,    # 短期借款
                "notes_payable": 5.0,       # 应付票据
                "accounts_payable": 30.0,   # 应付账款
                "advance_receipts": 10.0,   # 预收款项/合同负债
                "other_payables": 5.0,      # 其他应付款
                "lt_borrowing": 30.0,       # 长期借款
                "bonds_payable": 10.0,      # 应付债券
                "lease_liability": 5.0,     # 租赁负债
                "total_equity": 300.0,      # 所有者权益合计
                "parent_equity": 280.0,     # 归母所有者权益
            }, ...
        ],
        "cashflow": [
            {
                "year": 2020,
                "operating_cf": 45.0,       # 经营活动现金流净额
                "sales_cash": 110.0,        # 销售商品提供劳务收到的现金
                "investing_cf": -30.0,      # 投资活动现金流净额
                "capex": 25.0,              # 购建固定资产等支付的现金
                "financing_cf": -10.0,      # 筹资活动现金流净额
                "dividend_paid": 15.0,      # 分配股利/偿付利息支付的现金
                "cash_end": 105.0,          # 期末现金及现金等价物余额
            }, ...
        ]
    }
    """
    
    data = {
        "meta": {
            "code": code,
            "name": name or raw_data.get("company", {}).get("name", ""),
            "market": raw_data.get("company", {}).get("market", ""),
            "industry": raw_data.get("company", {}).get("industry", ""),
            "ipo_date": raw_data.get("company", {}).get("ipo_date", ""),
        },
        "raw": raw_data,
        "processed": {}
    }
    
    # 处理财务数据
    income_data = raw_data.get("income", [])
    balance_data = raw_data.get("balance", [])
    cashflow_data = raw_data.get("cashflow", [])
    price_data = raw_data.get("stock_price", [])
    
    if not income_data:
        print("⚠️ 缺少利润表数据，跳过处理", file=sys.stderr)
        return data
    
    years = len(income_data)
    first_year = income_data[0]["year"]
    last_year = income_data[-1]["year"]
    
    # ===== 利润表计算 =====
    processed = {
        "years": [d["year"] for d in income_data],
        "revenue": [d.get("operating_revenue", d.get("revenue", 0)) for d in income_data],
        "net_profit": [d.get("parent_net_profit", 0) for d in income_data],
        "total_profit": [d.get("total_profit", 0) for d in income_data],
        "gross_margin": [],
        "net_margin": [],
        "operating_margin": [],
        "fee_rate": [],
        "sell_fee_rate": [],
        "admin_fee_rate": [],
        "finance_fee_rate": [],
        "rd_fee_rate": [],
    }
    
    for d in income_data:
        rev = d.get("operating_revenue", d.get("revenue", 1))
        if rev <= 0:
            rev = 1  # 避免除零
        
        cost = d.get("operating_cost", 0)
        gross = rev - cost
        
        processed["gross_margin"].append(round(gross / rev * 100, 2))
        processed["net_margin"].append(round(d.get("parent_net_profit", 0) / rev * 100, 2))
        processed["operating_margin"].append(round(d.get("operating_profit", 0) / rev * 100, 2))
        
        # 费用率 (不含财务费用为正时)
        sell = d.get("sell_expense", 0)
        admin = d.get("admin_expense", 0)
        finance = d.get("finance_expense", 0)
        rd = d.get("rd_expense", 0)
        
        if finance > 0:
            total_fee = sell + admin + finance + rd
        else:
            total_fee = sell + admin + rd
        processed["fee_rate"].append(round(total_fee / rev * 100, 2))
        
        processed["sell_fee_rate"].append(round(sell / rev * 100, 2) if sell else 0)
        processed["admin_fee_rate"].append(round(admin / rev * 100, 2) if admin else 0)
        processed["finance_fee_rate"].append(round(finance / rev * 100, 2) if finance else 0)
        processed["rd_fee_rate"].append(round(rd / rev * 100, 2) if rd else 0)
    
    # 年化增长率
    processed["revenue_cagr"] = calc_cagr(
        processed["revenue"][0], processed["revenue"][-1], years - 1
    )
    processed["net_profit_cagr"] = calc_cagr(
        processed["net_profit"][0], processed["net_profit"][-1], years - 1
    )
    
    # ===== 股价计算 =====
    if price_data:
        price_years = [d["year"] for d in price_data]
        prices = [d["close"] for d in price_data]
        processed["price_years"] = price_years
        processed["stock_prices"] = prices
        processed["price_cagr"] = calc_cagr(prices[0], prices[-1], len(prices) - 1)
    
    # ===== 资产负债表计算 =====
    b_processed = {
        "total_assets": [],
        "interest_bearing_debt": [],      # 有息负债
        "interest_bearing_debt_ratio": [], # 有息负债/总资产
        "prod_assets": [],                 # 生产资产
        "prod_asset_ratio": [],            # 生产资产/总资产
        "biz_assets": [],                  # 经营资产
        "invest_assets": [],               # 投资资产
        "receivables": [],                 # 应收款项
        "receivable_ratio": [],            # 应收/总资产
        "cash_balance": [],                # 货币资金
        "non_core_asset_ratio": [],        # 非主业资产/总资产
        "total_equity": [],
        "total_liability_ratio": [],
        "current_ratio": [],
        "quick_ratio": [],
    }
    
    for d in balance_data:
        ta = d.get("total_assets", 1)
        if ta <= 0:
            ta = 1
        
        # 有息负债
        ibd = (d.get("short_borrowing", 0) + d.get("lt_borrowing", 0) 
               + d.get("bonds_payable", 0) + d.get("lease_liability", 0))
        
        # 生产资产 = 固定资产 + 在建工程 + 使用权资产 + 无形资产(土地部分估算50%)
        prod = (d.get("fixed_assets", 0) + d.get("construction", 0) 
                + d.get("right_of_use", 0) + d.get("intangible_assets", 0) * 0.5)
        
        # 经营资产
        biz = (d.get("cash", 0) + d.get("inventory", 0) 
               + d.get("notes_receivable", 0) + d.get("accounts_receivable", 0)
               + d.get("prepayments", 0) + d.get("other_receivables", 0))
        
        # 投资资产
        invest = (d.get("lt_equity_invest", 0) + d.get("trading_financial", 0)
                  + d.get("other_financial", 0) + d.get("invest_real_estate", 0)
                  + d.get("goodwill", 0))
        
        # 应收款项
        recv = (d.get("notes_receivable", 0) + d.get("accounts_receivable", 0)
                + d.get("other_receivables", 0))
        
        # 非主业资产
        non_core = (d.get("trading_financial", 0) + d.get("other_financial", 0)
                    + d.get("invest_real_estate", 0) + d.get("lt_equity_invest", 0))
        
        b_processed["total_assets"].append(ta)
        b_processed["interest_bearing_debt"].append(round(ibd, 2))
        b_processed["interest_bearing_debt_ratio"].append(round(ibd / ta * 100, 2))
        b_processed["prod_assets"].append(round(prod, 2))
        b_processed["prod_asset_ratio"].append(round(prod / ta * 100, 2))
        b_processed["biz_assets"].append(round(biz, 2))
        b_processed["invest_assets"].append(round(invest, 2))
        b_processed["receivables"].append(round(recv, 2))
        b_processed["receivable_ratio"].append(round(recv / ta * 100, 2))
        b_processed["cash_balance"].append(d.get("cash", 0))
        b_processed["non_core_asset_ratio"].append(round(non_core / ta * 100, 2))
        b_processed["total_equity"].append(d.get("total_equity", 0))
        b_processed["total_liability_ratio"].append(
            round(d.get("total_liabilities", 0) / ta * 100, 2)
        )
        
        # 流动性指标
        ca = d.get("current_assets", 0)
        cl = d.get("current_liabilities", 1)
        inv = d.get("inventory", 0)
        b_processed["current_ratio"].append(round(ca / cl, 2) if cl else 0)
        b_processed["quick_ratio"].append(round((ca - inv) / cl, 2) if cl else 0)
    
    # ===== 现金流量表计算 =====
    c_processed = {
        "operating_cf": [],
        "investing_cf": [],
        "financing_cf": [],
        "sales_cash": [],
        "capex": [],
        "dividend_paid": [],
        "cash_end": [],
        "cf_portrait": [],          # 现金流肖像 [经营,投资,筹资]
        "ocf_to_np": [],            # 经营现金流/净利润
        "sales_cash_to_rev": [],    # 销售收现/营收
        "cash_debt_ratio": [],      # 现金债务比
    }
    
    for i, d in enumerate(cashflow_data):
        ocf = d.get("operating_cf", 0)
        icf = d.get("investing_cf", 0)
        fcf = d.get("financing_cf", 0)
        
        c_processed["operating_cf"].append(ocf)
        c_processed["investing_cf"].append(icf)
        c_processed["financing_cf"].append(fcf)
        c_processed["sales_cash"].append(d.get("sales_cash", 0))
        c_processed["capex"].append(d.get("capex", 0))
        c_processed["dividend_paid"].append(d.get("dividend_paid", 0))
        c_processed["cash_end"].append(d.get("cash_end", 0))
        
        # 现金流肖像
        portrait = [
            "+" if ocf >= 0 else "-",
            "+" if icf >= 0 else "-",
            "+" if fcf >= 0 else "-",
        ]
        c_processed["cf_portrait"].append(portrait)
        
        # 净利润含金量
        np = processed["net_profit"][i] if i < len(processed["net_profit"]) else 0
        c_processed["ocf_to_np"].append(round(ocf / np, 2) if np else None)
        
        # 收现/营收
        rev = processed["revenue"][i] if i < len(processed["revenue"]) else 0
        c_processed["sales_cash_to_rev"].append(
            round(d.get("sales_cash", 0) / rev, 2) if rev else None
        )
        
        # 现金债务比
        ibd = b_processed["interest_bearing_debt"][i] if i < len(b_processed["interest_bearing_debt"]) else 0
        c_processed["cash_debt_ratio"].append(
            round(d.get("cash_end", 0) / ibd, 2) if ibd else None
        )
    
    # ===== ROE计算 =====
    roe_data = {
        "roe": [],
        "roa": [],
        "equity_multiplier": [],
        "asset_turnover": [],
    }
    
    for i, d in enumerate(income_data):
        np = d.get("parent_net_profit", 0)
        rev = processed["revenue"][i] if i < len(processed["revenue"]) else 0
        
        # 平均净资产
        if i < len(balance_data):
            eq_current = balance_data[i].get("total_equity", 0)
            eq_prev = balance_data[i-1].get("total_equity", eq_current) if i > 0 else eq_current
            avg_equity = (eq_current + eq_prev) / 2
            avg_ta = (balance_data[i].get("total_assets", 0) + balance_data[i-1].get("total_assets", 0)) / 2 if i > 0 else balance_data[i].get("total_assets", 0)
        else:
            avg_equity = 1
            avg_ta = 1
        
        roe = round(np / avg_equity * 100, 2) if avg_equity else 0
        roa = round(np / avg_ta * 100, 2) if avg_ta else 0
        
        # 权益乘数
        if i < len(balance_data):
            em = balance_data[i].get("total_assets", 0) / balance_data[i].get("total_equity", 1)
        else:
            em = 0
        
        # 总资产周转率
        ato = round(rev / avg_ta, 2) if avg_ta else 0
        
        roe_data["roe"].append(roe)
        roe_data["roa"].append(roa)
        roe_data["equity_multiplier"].append(round(em, 2))
        roe_data["asset_turnover"].append(ato)
    
    # ===== 净利润率 =====
    processed["net_profit_margin"] = [
        round(roe_data["roe"][i] / max(roe_data["asset_turnover"][i], 0.01) / max(roe_data["equity_multiplier"][i], 0.01), 2)
        if i < len(roe_data["asset_turnover"]) and i < len(roe_data["equity_multiplier"])
        else processed["net_margin"][i]
        for i in range(len(processed["net_margin"]))
    ]
    
    # ===== 资产结构百分比（最新一期）=====
    if balance_data:
        latest = balance_data[-1]
        prod = b_processed["prod_assets"][-1]
        biz = b_processed["biz_assets"][-1]
        invest = b_processed["invest_assets"][-1]
        
        processed["latest_asset_structure"] = {
            "生产资产": round(prod, 2),
            "经营资产": round(biz, 2),
            "投资资产": round(invest, 2),
            "其他": round(latest.get("total_assets", 0) - prod - biz - invest, 2),
        }
    
    # ===== 营收切分（最新一期）=====
    if income_data:
        latest_inc = income_data[-1]
        rev = processed["revenue"][-1]
        if rev > 0:
            processed["revenue_split"] = {
                "毛利": round(latest_inc.get("gross_profit", 0) / rev * 100, 2),
                "销售费用": round(latest_inc.get("sell_expense", 0) / rev * 100, 2),
                "管理费用": round(latest_inc.get("admin_expense", 0) / rev * 100, 2),
                "研发费用": round(latest_inc.get("rd_expense", 0) / rev * 100, 2),
                "财务费用": round(latest_inc.get("finance_expense", 0) / rev * 100, 2),
                "税金及附加": round(latest_inc.get("operating_profit", 0) / rev * 100, 2),  # 需要单独取税金数据
                "所得税": round(latest_inc.get("income_tax", 0) / rev * 100, 2),
                "净利润": round(latest_inc.get("parent_net_profit", 0) / rev * 100, 2),
                "少数股东损益": round(latest_inc.get("minority_interest", 0) / rev * 100, 2),
            }
    
    # ===== 同行对比数据占位 =====
    processed["peer_comparison"] = None  # 由 Agent 在分析时填充
    
    # ===== 成长性指标 =====
    processed["revenue_growth"] = []
    processed["profit_growth"] = []
    processed["asset_growth"] = []
    processed["equity_growth"] = []
    
    for i in range(1, len(processed["revenue"])):
        cur_rev = processed["revenue"][i]
        prev_rev = processed["revenue"][i-1]
        processed["revenue_growth"].append(
            round((cur_rev - prev_rev) / prev_rev * 100, 2) if prev_rev else 0
        )
        
        cur_np = processed["net_profit"][i]
        prev_np = processed["net_profit"][i-1]
        processed["profit_growth"].append(
            round((cur_np - prev_np) / abs(prev_np) * 100, 2) if prev_np else 0
        )
    
    for i in range(1, len(b_processed["total_assets"])):
        cur_ta = b_processed["total_assets"][i]
        prev_ta = b_processed["total_assets"][i-1]
        processed["asset_growth"].append(
            round((cur_ta - prev_ta) / prev_ta * 100, 2) if prev_ta else 0
        )
        
        cur_eq = b_processed["total_equity"][i]
        prev_eq = b_processed["total_equity"][i-1]
        processed["equity_growth"].append(
            round((cur_eq - prev_eq) / prev_eq * 100, 2) if prev_eq else 0
        )
    
    # 管理层能力指标
    processed["receivable_turnover"] = []
    processed["inventory_turnover"] = []
    processed["fixed_asset_turnover"] = []
    processed["total_asset_turnover"] = []
    
    for i, d in enumerate(income_data):
        rev = processed["revenue"][i]
        
        if i < len(balance_data):
            # 应收账款周转率
            ar = balance_data[i].get("accounts_receivable", 0)
            ar_prev = balance_data[i-1].get("accounts_receivable", ar) if i > 0 else ar
            avg_ar = (ar + ar_prev) / 2
            processed["receivable_turnover"].append(
                round(rev / avg_ar, 2) if avg_ar else 0
            )
            
            # 存货周转率
            cost = d.get("operating_cost", 0)
            inv = balance_data[i].get("inventory", 0)
            inv_prev = balance_data[i-1].get("inventory", inv) if i > 0 else inv
            avg_inv = (inv + inv_prev) / 2
            processed["inventory_turnover"].append(
                round(cost / avg_inv, 2) if avg_inv else 0
            )
            
            # 固定资产周转率
            fa = balance_data[i].get("fixed_assets", 0)
            processed["fixed_asset_turnover"].append(
                round(rev / fa, 2) if fa else 0
            )
            
            # 总资产周转率
            ta = balance_data[i].get("total_assets", 0)
            ta_prev = balance_data[i-1].get("total_assets", ta) if i > 0 else ta
            avg_ta = (ta + ta_prev) / 2
            processed["total_asset_turnover"].append(
                round(rev / avg_ta, 2) if avg_ta else 0
            )
    
    # 组装所有处理结果
    data["processed"]["income"] = processed
    data["processed"]["balance"] = b_processed
    data["processed"]["cashflow"] = c_processed
    data["processed"]["roe"] = roe_data
    
    return data


def main():
    args = parse_args()
    
    # 加载原始数据
    if args.raw:
        with open(args.raw, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    else:
        # 从标准输入读取
        raw_data = json.load(sys.stdin)
    
    # 处理数据
    result = process_financial_data(raw_data, args.code, args.name)
    
    # 输出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已处理并保存至: {output_path}")
    print(f"   公司: {result['meta']['name']} ({result['meta']['code']})")
    print(f"   数据年份: {result['processed']['income']['years'][0]} - {result['processed']['income']['years'][-1]}")
    
    if result["processed"]["income"].get("revenue_cagr"):
        print(f"   营收年化增长: {result['processed']['income']['revenue_cagr']:.2f}%")
    if result["processed"]["income"].get("net_profit_cagr"):
        print(f"   净利年化增长: {result['processed']['income']['net_profit_cagr']:.2f}%")


if __name__ == "__main__":
    main()
