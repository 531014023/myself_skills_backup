#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
年报PDF数据提取脚本 - 智能字段适配版
支持任意字段的自动提取，无需预定义
"""

import os
import sys
import re
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import pdfplumber
except ImportError:
    print("错误：缺少 pdfplumber 库。请运行: pip install pdfplumber")
    sys.exit(1)

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class SmartPDFExtractor:
    """智能PDF数据提取器，支持任意字段"""
    
    def __init__(self, fields: List[str] = None):
        self.fields = fields or ['营业收入']
        
    def extract_from_pdf(self, pdf_path: str, use_ocr: bool = False) -> Dict:
        """从PDF中提取数据"""
        if not use_ocr:
            result = self._extract_text_and_tables(pdf_path)
            if result:
                return result
        
        if PDF2IMAGE_AVAILABLE and TESSERACT_AVAILABLE:
            return self._extract_with_ocr(pdf_path)
        else:
            return {"file": pdf_path, "error": "缺少OCR库"}
    
    def _extract_text_and_tables(self, pdf_path: str) -> Dict:
        """提取文本和表格"""
        text = ""
        tables_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages[:30]):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            tables_data.extend(table)
        except Exception as e:
            print(f"  提取文本失败: {e}")
            return None
        
        return self._parse_content(text, tables_data, pdf_path)
    
    def _extract_with_ocr(self, pdf_path: str) -> Dict:
        """OCR提取"""
        print(f"  使用OCR处理: {pdf_path}")
        try:
            images = convert_from_path(pdf_path, dpi=300)
            all_text = ""
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                all_text += text + "\n"
            return self._parse_content(all_text, [], pdf_path)
        except Exception as e:
            return {"file": pdf_path, "error": str(e)}
    
    def _generate_patterns(self, field_name: str) -> List[str]:
        """为字段生成提取模式"""
        # 基础模式
        patterns = [
            rf'{field_name}[：:]\s*([\d,\.]+)',
            rf'([\d,\.]+)\s*(?:万元|亿元|元).*{field_name}',
            rf'{field_name}.*?([\d,\.]+)\s*(?:万元|亿元|元)',
        ]
        return patterns
    
    def _parse_content(self, text: str, tables_data: List, source: str) -> Dict:
        """解析内容，智能提取所有字段"""
        result = {"file": source}
        lines = text.split('\n')
        
        for field_name in self.fields:
            all_matches = []
            
            # 生成字段的提取模式
            patterns = self._generate_patterns(field_name)
            
            # 在文本中查找
            for i, line in enumerate(lines):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        cleaned = self._clean_number(match)
                        try:
                            val_float = float(cleaned)
                            # 过滤明显不合理的值
                            if val_float > 1000000:  # 大于100万
                                all_matches.append((val_float, cleaned, i))
                        except:
                            pass
            
            # 在表格中查找
            table_matches = self._extract_from_tables(tables_data, field_name)
            all_matches.extend(table_matches)
            
            # 选择最佳匹配
            if all_matches:
                # 策略1：如果有多个匹配，选择最大的（通常是年度总计）
                all_matches.sort(reverse=True, key=lambda x: x[0])
                
                # 策略2：排除包含"期初"、"年初"等词的行（选期末数据）
                filtered = []
                for val, str_val, line_idx in all_matches:
                    context = ' '.join(lines[max(0, line_idx-2):min(len(lines), line_idx+3)])
                    if not any(kw in context for kw in ['期初', '年初', '上期', '期初余额', '年初余额']):
                        filtered.append((val, str_val))
                
                if filtered:
                    result[field_name] = filtered[0][1]
                else:
                    result[field_name] = all_matches[0][1]
            else:
                result[field_name] = "未找到"
        
        return result
    
    def _extract_from_tables(self, tables_data: List, field_name: str) -> List[Tuple[float, str, int]]:
        """从表格中提取"""
        matches = []
        
        for row in tables_data:
            if not row:
                continue
            row_text = ' '.join(str(cell) for cell in row if cell)
            
            if field_name in row_text:
                # 查找行中的数字
                numbers = re.findall(r'[\d,\.]+', row_text)
                for num in numbers:
                    try:
                        val_float = float(num.replace(',', ''))
                        if val_float > 1000000:  # 大于100万
                            matches.append((val_float, self._clean_number(num), 0))
                    except:
                        pass
        
        return matches
    
    def _clean_number(self, value: str) -> str:
        """清理数字"""
        if isinstance(value, str):
            value = value.replace(",", "").replace(" ", "").strip()
        return value


def extract_year_from_filename(filename: str) -> Optional[int]:
    """从文件名提取年份"""
    # 优先匹配年报年份格式
    match = re.search(r'贵州茅台[_]?(\d{4})年年度报告', filename)
    if match:
        return int(match.group(1))
    
    # 备选：匹配任意4位年份
    match = re.search(r'(20\d{2})', filename)
    if match:
        return int(match.group(1))
    
    return None


def main():
    parser = argparse.ArgumentParser(description='从年报PDF中提取数据 - 支持任意字段')
    parser.add_argument('pdf_files', nargs='+', help='PDF文件路径')
    parser.add_argument('-o', '--output', help='输出CSV文件路径', default='extracted_data.csv')
    parser.add_argument('--ocr', action='store_true', help='强制使用OCR')
    parser.add_argument('--fields', help='要提取的字段，用逗号分隔', default='营业收入')
    
    args = parser.parse_args()
    
    # 解析字段
    field_names = [f.strip() for f in args.fields.split(',')]
    
    # 创建提取器
    extractor = SmartPDFExtractor(field_names)
    
    # 处理PDF文件
    results = []
    print(f"开始处理 {len(args.pdf_files)} 个PDF文件...")
    print(f"提取字段: {', '.join(field_names)}\n")
    
    for pdf_file in args.pdf_files:
        if not os.path.exists(pdf_file):
            print(f"警告：文件不存在 {pdf_file}")
            continue
        
        filename = os.path.basename(pdf_file)
        print(f"处理: {filename}")
        
        result = extractor.extract_from_pdf(pdf_file, use_ocr=args.ocr)
        
        # 添加年份
        year = extract_year_from_filename(filename)
        result['year'] = year if year else "未知"
        
        results.append(result)
        
        # 显示结果
        for field in field_names:
            value = result.get(field, '未找到')
            if value and value != '未找到':
                try:
                    val_float = float(value)
                    if val_float > 100000000:
                        print(f"  [OK] {field}: {val_float/100000000:.2f} 亿元")
                    else:
                        print(f"  [OK] {field}: {value}")
                except:
                    print(f"  [OK] {field}: {value}")
            else:
                print(f"  [FAIL] {field}: 未找到")
        print()
    
    # 输出CSV
    if results:
        # 构建列名
        fieldnames = ['file', 'year']
        for field in field_names:
            fieldnames.append(f"{field}(亿元)")
            fieldnames.append(f"{field}(元)")
        
        # 转换数据
        csv_results = []
        for result in results:
            csv_row = {'file': result['file'], 'year': result['year']}
            for field in field_names:
                value = result.get(field, '未找到')
                csv_row[f"{field}(元)"] = value
                if value and value != '未找到':
                    try:
                        val_float = float(value)
                        csv_row[f"{field}(亿元)"] = f"{val_float/100000000:.2f}"
                    except:
                        csv_row[f"{field}(亿元)"] = '未找到'
                else:
                    csv_row[f"{field}(亿元)"] = '未找到'
            csv_results.append(csv_row)
        
        with open(args.output, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_results)
        
        print(f"{'='*60}")
        print(f"数据已保存到: {args.output}")
        print(f"成功处理 {len(results)} 个文件")
        print(f"{'='*60}")
    else:
        print("没有成功提取任何数据")


if __name__ == '__main__':
    main()
