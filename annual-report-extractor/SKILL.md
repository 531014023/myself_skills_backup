---
name: annual-report-extractor
description: 从年报PDF中提取数值型财务数据和产能数据。当用户使用自然语言指令如"提取贵州茅台2015-2024年的营业收入"、"从这些PDF中获取净利润"、"提取茅台酒产能数据"或"获取设计产能和实际产能"时触发。自动解析公司名称、年份范围和数据字段。支持产能数据和财务数据提取，输出CSV格式。
---

# 年报PDF数据提取

## 全局规则

**所有输出必须使用中文回答。**

- 所有界面提示信息使用中文
- 所有错误信息使用中文
- 所有状态报告使用中文
- 所有结果展示使用中文
- CSV文件的列名使用中文

---

从企业年报PDF中提取指定字段的数值数据。用户通过自然语言描述提取需求，自动解析公司名、年份范围和数据字段，支持原生PDF和扫描版PDF（OCR），输出CSV格式。

从企业年报PDF中提取指定字段的数值数据。用户通过自然语言描述提取需求，自动解析公司名、年份范围和数据字段，支持原生PDF和扫描版PDF（OCR），输出CSV格式。

## 核心特性：任意字段自动适配

本技能采用**智能字段识别技术**，无需预定义即可提取任意财务字段：

✅ **自动适配任意字段**：无论是"营业收入"、"存货"、"应收账款"还是"商誉"，只要PDF中包含该字段，就能自动提取
✅ **智能模式生成**：根据字段名称自动生成多种提取模式
✅ **智能去重筛选**：自动排除"期初"、"年初"等期初数据，选择期末数据
✅ **多字段同时提取**：支持一次提取多个字段，如"存货,应收账款,固定资产"

## 支持的数据类型

### 产能数据
- 设计产能、实际产能、产能利用率
- 茅台酒产能、系列酒产能
- 产量、生产量

### 常用财务指标
- 营业收入、营业成本、营业利润
- 净利润、归母净利润、扣非净利润
- 总资产、总负债、净资产
- 货币资金、存货、应收账款
- 固定资产、无形资产、商誉
- 经营现金流、投资现金流、筹资现金流
- 每股收益、每股净资产、每股现金流
- 资产负债率、毛利率、净利率、ROE

**自定义字段**：
- 任何在年报中出现的财务科目名称
- 支持中文和英文字段名
- 支持同时提取多个字段

## 触发条件

当用户在聊天框输入以下类型的指令时触发：

**产能数据提取：**
- "提取茅台酒的设计产能和实际产能"
- "从年报中获取产能数据"
- "茅台酒产能利用率"
- "系列酒产能和产量"

**财务数据提取：**
- "提取贵州茅台2015-2024年的营业收入"
- "帮我获取这些年报里的净利润数据"
- "从PDF中提取总资产和净资产"
- "OCR扫描版年报，提取营业收入"

## 工作流程

当技能被触发时，立即执行以下操作：

### 1. 解析用户指令

从用户输入中提取：
- **公司名**：识别公司名称（如：贵州茅台）
- **年份范围**：解析 "2015-2024"、"2020到2023年" 等格式
- **数据字段**：营业收入、净利润、总资产、净资产、每股收益、员工人数等
- **OCR模式**：检测是否提到"扫描"、"OCR"等关键词

解析代码：
```python
import re
import os
import glob

def parse_request(user_input):
    result = {'company': None, 'years': [], 'fields': [], 'use_ocr': False}
    
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
    
    # 字段解析
    field_map = {
        '营业收入': ['营业收入', '营业总收入', '营收'],
        '净利润': ['净利润', '净利', '归属于'],
        '总资产': ['总资产', '资产总计'],
        '净资产': ['净资产', '所有者权益', '股东权益'],
        '每股收益': ['每股收益', 'eps'],
        '员工人数': ['员工', '职工', '人数'],
        '毛利率': ['毛利率'],
        '资产负债率': ['资产负债率', '负债率']
    }
    
    for field, keywords in field_map.items():
        if any(kw in user_input for kw in keywords):
            result['fields'].append(field)
    
    if not result['fields']:
        result['fields'] = ['营业收入']  # 默认字段
    
    return result
```

### 2. 查找PDF文件

在当前目录查找匹配的年报PDF：
```python
def find_pdfs(company, years):
    pdfs = []
    for pdf in glob.glob('*.pdf'):
        filename = os.path.basename(pdf)
        
        # 年份匹配
        if years:
            file_years = re.findall(r'20\d{2}', filename)
            if not any(int(y) in years for y in file_years):
                continue
        
        # 公司名匹配（如果指定）
        if company and company not in filename:
            continue
            
        pdfs.append(pdf)
    
    return sorted(pdfs, key=lambda x: re.findall(r'20\d{2}', x)[0] if re.findall(r'20\d{2}', x) else '0')
```

### 3. 执行数据提取

调用路由器脚本自动选择合适的提取器：
```python
import subprocess
import sys
from pathlib import Path

CAPACITY_KEYWORDS = ['产能', '产量', '设计产能', '实际产能']
FINANCIAL_KEYWORDS = ['营业收入', '净利润', '总资产', '利润']

def route_and_extract(user_input, pdf_files):
    skill_dir = Path(__file__).parent
    router_script = skill_dir / 'scripts' / 'extract_router.py'
    
    cmd = [
        sys.executable,
        str(router_script),
        user_input,
        *pdf_files
    ]
    
    subprocess.run(cmd)
```

**自动路由规则：**
- 用户请求包含"产能"、"产量"等关键词 → 自动调用 `extract_capacity.py`
- 用户请求包含"营业收入"、"净利润"等财务关键词 → 自动调用 `extract_data.py`

### 4. 输出结果

- 显示解析出的公司、年份、字段信息
- 列出找到的PDF文件
- 显示提取进度
- 报告CSV文件保存位置

## 内置提取规则

脚本内置以下字段的自动提取规则：

```python
FIELD_PATTERNS = {
    '营业收入': {
        'keywords': ['营业收入', '营业总收入', '主营业务收入', '营收'],
        'patterns': [
            r'营业收入[：:]\s*([\d,\.]+)',
            r'营业总收入[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)\s*(万元|亿元|元).*营业收入'
        ]
    },
    '净利润': {
        'keywords': ['净利润', '归属于母公司股东的净利润', '净利'],
        'patterns': [
            r'净利润[：:]\s*([\d,\.]+)',
            r'归属于.*?净利润[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)\s*(万元|亿元|元).*净利润'
        ]
    },
    '总资产': {
        'keywords': ['总资产', '资产总计', '资产总额'],
        'patterns': [
            r'总资产[：:]\s*([\d,\.]+)',
            r'资产总计[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)\s*(万元|亿元|元).*总资产'
        ]
    },
    '净资产': {
        'keywords': ['净资产', '所有者权益', '股东权益'],
        'patterns': [
            r'净资产[：:]\s*([\d,\.]+)',
            r'所有者权益[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)\s*(万元|亿元|元).*净资产'
        ]
    },
    '每股收益': {
        'keywords': ['每股收益', '基本每股收益', 'eps'],
        'patterns': [
            r'每股收益[：:]\s*([\d,\.]+)',
            r'基本每股收益[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)\s*元.*每股收益'
        ]
    },
    '员工人数': {
        'keywords': ['员工', '职工', '人数', 'employees'],
        'patterns': [
            r'员工[人数]*[：:]\s*([\d,\.]+)',
            r'职工[人数]*[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)\s*人'
        ]
    },
    '毛利率': {
        'keywords': ['毛利率', 'gross margin'],
        'patterns': [
            r'毛利率[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)%.*毛利率'
        ]
    },
    '资产负债率': {
        'keywords': ['资产负债率', '负债率'],
        'patterns': [
            r'资产负债率[：:]\s*([\d,\.]+)',
            r'([\d,\.]+)%.*资产负债率'
        ]
    }
}
```

## 完整执行代码

当用户输入自然语言指令时，执行以下完整代码：

```python
import re
import os
import glob
import subprocess
import sys
from pathlib import Path

CAPACITY_KEYWORDS = ['产能', '产量', '设计产能', '实际产能']

def parse_request(user_input):
    result = {
        'years': [],
        'fields': [],
        'use_ocr': False,
        'extract_type': 'financial'
    }
    
    if any(kw in user_input.lower() for kw in ['ocr', '扫描', '图片']):
        result['use_ocr'] = True
    
    year_matches = re.findall(r'(20\d{2})\s*[-至到~]\s*(20\d{2})', user_input)
    if year_matches:
        for start, end in year_matches:
            result['years'].extend(range(int(start), int(end) + 1))
    else:
        years = re.findall(r'(20\d{2})\s*年?', user_input)
        result['years'] = [int(y) for y in years]
    result['years'] = sorted(list(set(result['years'])))
    
    if any(kw in user_input for kw in CAPACITY_KEYWORDS):
        result['extract_type'] = 'capacity'
    
    return result

def find_pdfs(years):
    pdfs = []
    for pdf in glob.glob('pdf/*.pdf'):
        if years:
            file_years = re.findall(r'(20\d{2})', pdf)
            if not any(int(y) in years for y in file_years):
                continue
        pdfs.append(pdf)
    return sorted(pdfs, key=lambda x: re.findall(r'(20\d{2})', x)[0])

def extract_data(pdf_files, extract_type):
    skill_dir = Path(__file__).parent
    
    if extract_type == 'capacity':
        script = skill_dir / 'scripts' / 'extract_capacity.py'
        output_file = '产能数据.csv'
    else:
        script = skill_dir / 'scripts' / 'extract_data.py'
        output_file = f"extracted_data.csv"
    
    cmd = [sys.executable, str(script), '-o', output_file] + pdf_files
    subprocess.run(cmd)
    return output_file

user_input = """{{USER_INPUT}}"""

parsed = parse_request(user_input)
print(f"📋 解析结果:")
print(f"   提取类型: {'产能数据' if parsed['extract_type'] == 'capacity' else '财务数据'}")
print(f"   年份: {', '.join(map(str, parsed['years'])) if parsed['years'] else '所有年份'}")

pdf_files = find_pdfs(parsed['years'])

if not pdf_files:
    print("\n❌ 未找到匹配的PDF文件")
else:
    print(f"\n✓ 找到 {len(pdf_files)} 个PDF文件")
    print(f"\n🚀 开始提取...")
    output = extract_data(pdf_files, parsed['extract_type'])
    print(f"\n✅ 提取完成！数据已保存到: {output}")
```

## 依赖要求

执行前确保已安装：
```bash
# 必需
pip install pdfplumber

# OCR支持（可选）
pip install pdf2image pytesseract pillow
```

Windows用户还需安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)

## 输出格式

**财务数据CSV格式：**
```csv
file,year,营业收入,营业收入(亿元)
贵州茅台_2020年报.pdf,2020,97993286520.21,979.93
贵州茅台_2021年报.pdf,2021,106190257678.13,1061.90
```

**产能数据CSV格式：**
```csv
file,year,设计产能_茅台酒,实际产能_茅台酒,设计产能_系列酒,实际产能_系列酒
贵州茅台_2020年报.pdf,2020,42560,50235.17,25260,24925.37
贵州茅台_2021年报.pdf,2021,42742.50,56472.25,31660,28248.92
```

## 注意事项

1. **PDF命名**：文件名应包含年份信息（如 `贵州茅台_2023年报.pdf`），方便自动匹配
2. **字段匹配**：如果某个字段未找到，CSV中会显示"未找到"
3. **OCR模式**：扫描版PDF会自动检测，或用户可明确说明使用OCR
4. **多字段**：可同时提取多个字段，如"营业收入和净利润"
5. **中文支持**：确保系统支持中文显示和OCR识别

## 产能数据提取功能

本技能新增产能数据专项提取能力：

### 支持的产能字段
- **设计产能**：茅台酒/系列酒的设计产能（吨）
- **实际产能**：茅台酒/系列酒的实际产量（吨）
- **产能利用率**：实际产能/设计产能百分比

### 产能数据特点
- 从年报表格中精准提取产能数据
- 自动识别产能和产量相关表格
- 支持茅台酒和系列酒分别提取
- 自动计算并展示产能利用率

### 触发示例
- "提取茅台酒的设计产能和实际产能"
- "从2014-2024年报中获取产能数据"
- "茅台酒的产能利用率"
- "系列酒产能和产量趋势"
