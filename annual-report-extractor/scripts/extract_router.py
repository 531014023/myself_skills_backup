#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
年报数据提取路由器
根据用户请求类型自动选择合适的提取脚本
"""

import os
import sys
import re
import glob
import subprocess
from pathlib import Path

CAPACITY_KEYWORDS = ['产能', '产量', '设计产能', '实际产能', '茅台酒产能', '系列酒产能']
FINANCIAL_KEYWORDS = ['营业收入', '净利润', '总资产', '净资产', '利润', '收入', '现金流', '资产负债', '毛利率']

def parse_request(user_input: str) -> dict:
    """解析用户请求"""
    result = {
        'company': None,
        'years': [],
        'fields': [],
        'use_ocr': False,
        'extract_type': 'general'  # general 或 capacity
    }
    
    # OCR检测
    if any(kw in user_input.lower() for kw in ['ocr', '扫描', '图片']):
        result['use_ocr'] = True
    
    # 年份解析
    year_matches = re.findall(r'(20\d{2})\s*[-至到~]\s*(20\d{2})', user_input)
    if year_matches:
        for start, end in year_matches:
            result['years'].extend(range(int(start), int(end) + 1))
    else:
        years = re.findall(r'(20\d{2})\s*年?', user_input)
        result['years'] = [int(y) for y in years]
    result['years'] = sorted(list(set(result['years'])))
    
    # 提取类型判断
    if any(kw in user_input for kw in CAPACITY_KEYWORDS):
        result['extract_type'] = 'capacity'
    elif any(kw in user_input for kw in FINANCIAL_KEYWORDS):
        result['extract_type'] = 'financial'
    
    # 字段解析
    for kw in CAPACITY_KEYWORDS:
        if kw in user_input:
            result['fields'].append(kw)
    
    for kw in FINANCIAL_KEYWORDS:
        if kw in user_input:
            result['fields'].append(kw)
    
    if not result['fields']:
        result['fields'] = ['营业收入']
    
    return result

def find_pdfs(years: list) -> list:
    """查找PDF文件"""
    pdfs = []
    for pdf in glob.glob('pdf/*.pdf'):
        filename = os.path.basename(pdf)
        if years:
            file_years = re.findall(r'(20\d{2})', filename)
            if not any(int(y) in years for y in file_years):
                continue
        pdfs.append(pdf)
    return sorted(pdfs, key=lambda x: re.findall(r'(20\d{2})', x)[0])

def run_extraction(user_input: str):
    """执行提取"""
    parsed = parse_request(user_input)
    skill_dir = Path(__file__).parent
    
    print(f"📋 解析结果:")
    print(f"   提取类型: {'产能数据' if parsed['extract_type'] == 'capacity' else '财务数据'}")
    print(f"   年份: {', '.join(map(str, parsed['years'])) if parsed['years'] else '所有年份'}")
    print(f"   字段: {', '.join(parsed['fields'])}")
    
    pdf_files = find_pdfs(parsed['years'])
    
    if not pdf_files:
        print("\n❌ 未找到匹配的PDF文件")
        return
    
    print(f"\n✓ 找到 {len(pdf_files)} 个PDF文件")
    
    # 选择提取脚本
    if parsed['extract_type'] == 'capacity':
        script = skill_dir / 'extract_capacity.py'
        output_file = '产能数据.csv'
    else:
        script = skill_dir / 'extract_data.py'
        output_file = f"extracted_{'_'.join(parsed['fields'])}.csv"
    
    # 执行提取
    cmd = [sys.executable, str(script), '-o', output_file] + pdf_files
    
    print(f"\n🚀 开始提取...")
    subprocess.run(cmd)
    print(f"\n✅ 提取完成！数据已保存到: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_extraction(sys.argv[1])
    else:
        print("用法: python extract_router.py <用户请求>")
