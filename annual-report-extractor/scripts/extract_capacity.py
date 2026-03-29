#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
茅台酒产能数据提取脚本 - 精准版
从年报表格中提取产能数据
"""

import os
import re
import csv
import pdfplumber
from typing import Dict, List

def extract_capacity_from_pdf(pdf_path: str) -> Dict:
    """从PDF中提取产能数据"""
    result = {
        "file": os.path.basename(pdf_path),
        "year": None,
        "设计产能_茅台酒": "未找到",
        "实际产能_茅台酒": "未找到",
        "设计产能_系列酒": "未找到",
        "实际产能_系列酒": "未找到"
    }
    
    filename = os.path.basename(pdf_path)
    year_match = re.search(r'(20\d{2})年', filename)
    if year_match:
        result["year"] = int(year_match.group(1))
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:30]:
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # 查找产能表格 (通常有3列: 产品名称, 设计产能, 实际产能)
                    header = [str(c).strip() if c else "" for c in table[0]]
                    header_str = ' '.join(header).replace('\n', '')
                    
                    if '设计产能' in header_str and '实际产能' in header_str:
                        parse_capacity_table(table, result)
                        
    except Exception as e:
        print(f"  错误: {e}")
    
    return result

def parse_capacity_table(table: List, result: Dict):
    """解析产能表格"""
    for row in table[1:]:  # 跳过表头
        if not row or len(row) < 3:
            continue
        
        cells = [str(c).strip() if c else "" for cell in row for c in cell.split('\n')[:1]]
        row_text = ' '.join(cells)
        
        # 茅台酒行
        if '茅台酒' in row_text or ('茅台' in row_text and '酒' in row_text):
            # 找到设计产能和实际产能列
            for i, cell in enumerate(cells):
                cell_clean = cell.replace(',', '')
                if re.match(r'^[\d,\.]+$', cell_clean):
                    # 判断是设计产能还是实际产能
                    if result.get("设计产能_茅台酒", "未找到") == "未找到":
                        result["设计产能_茅台酒"] = cell_clean
                    elif result.get("实际产能_茅台酒", "未找到") == "未找到":
                        result["实际产能_茅台酒"] = cell_clean
                        break
        
        # 系列酒行
        if '系列酒' in row_text or '酱香系列' in row_text:
            for i, cell in enumerate(cells):
                cell_clean = cell.replace(',', '')
                if re.match(r'^[\d,\.]+$', cell_clean):
                    if result.get("设计产能_系列酒", "未找到") == "未找到":
                        result["设计产能_系列酒"] = cell_clean
                    elif result.get("实际产能_系列酒", "未找到") == "未找到":
                        result["实际产能_系列酒"] = cell_clean
                        break

def main():
    pdf_files = [
        "pdf/2015-04-21_600519_贵州茅台_2014年年度报告.pdf",
        "pdf/2016-03-24_600519_贵州茅台_2015年年度报告.pdf",
        "pdf/2017-04-15_600519_贵州茅台_2016年年度报告.pdf",
        "pdf/2018-03-28_600519_贵州茅台_2017年年度报告.pdf",
        "pdf/2019-03-29_600519_贵州茅台_2018年年度报告.pdf",
        "pdf/2020-04-22_600519_贵州茅台_2019年年度报告.pdf",
        "pdf/2021-03-31_600519_贵州茅台2020年年度报告.pdf",
        "pdf/2022-03-31_600519_贵州茅台2021年年度报告.pdf",
        "pdf/2023-03-31_600519_贵州茅台2022年年度报告.pdf",
        "pdf/2024-04-03_600519_贵州茅台2023年年度报告.pdf",
        "pdf/2025-04-03_600519_贵州茅台2024年年度报告.pdf"
    ]
    
    results = []
    print("="*70)
    print("贵州茅台酒产能数据提取 (2014-2024年)")
    print("="*70 + "\n")
    
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            continue
        
        print(f"处理: {os.path.basename(pdf_file)}")
        result = extract_capacity_from_pdf(pdf_file)
        results.append(result)
        
        print(f"  年份: {result['year']}")
        print(f"  茅台酒设计产能(吨): {result['设计产能_茅台酒']}")
        print(f"  茅台酒实际产能(吨): {result['实际产能_茅台酒']}")
        print()
    
    # 保存CSV
    output_file = "茅台酒产能数据.csv"
    fieldnames = ['file', 'year', '设计产能_茅台酒', '实际产能_茅台酒', '设计产能_系列酒', '实际产能_系列酒']
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print("="*70)
    print(f"提取完成! 数据已保存到: {output_file}")
    print(f"成功处理 {len(results)} 个文件")
    print("="*70)
    
    # 分析趋势
    print("\n" + "="*70)
    print("产能趋势分析")
    print("="*70)
    
    sorted_results = sorted([r for r in results if r['year']], key=lambda x: x['year'])
    
    print("\n年份\t设计产能\t实际产能\t利用率")
    print("-"*50)
    for r in sorted_results:
        design = r['设计产能_茅台酒']
        actual = r['实际产能_茅台酒']
        if design != "未找到" and actual != "未找到":
            try:
                design_val = float(design)
                actual_val = float(actual)
                rate = actual_val / design_val * 100 if design_val > 0 else 0
                print(f"{r['year']}\t{design_val:,.0f}\t\t{actual_val:,.0f}\t\t{rate:.1f}%")
            except:
                print(f"{r['year']}\t{design}\t\t{actual}\t\t-")
        else:
            print(f"{r['year']}\t{design}\t\t{actual}\t\t-")

if __name__ == '__main__':
    main()
