"""
巨潮资讯网年报下载器
支持A股（沪/深/北交所）和港股的年报、半年报、季报等定期报告
"""
import os
import sys
import re
import time
import datetime
import requests
from pathlib import Path

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded'
}

SEARCH_URL = "https://www.cninfo.com.cn/new/information/topSearch/query"
PLATE_URL = "https://www.cninfo.com.cn/new/disclosure/stock"
ANNOUNCEMENT_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
FILE_BASE_URL = "https://static.cninfo.com.cn/"

# 分类配置: (目录名, A股searchkey模板, 港股searchkey或(优先,备用), 报告类型)
# A股年报: "2024年年度报告" / 港股年报: "截至二零二五年十二月三十一日止年度全年业绩公布"
# 港股searchkey可以是字符串，也可以是元组(优先搜索, 备用搜索)，用于优先下载正式年报
CATEGORY_CONFIG = {
    '年报':   ('年报',   '{year}年年度报告', ('年报', '全年业绩'), 'annual'),
    '半年报': ('半年报', '{year}年半年度报告', '六个月业绩', 'half'),
    '一季报': ('一季报', '{year}年一季报',     '三个月业绩', 'q1'),
    '三季报': ('三季报', '{year}年三季报',     '九个月业绩', 'q3'),
}

# 港股标题中的中文数字年份 -> 阿拉伯数字
CN_DIGIT_MAP = {'零': '0', '一': '1', '二': '2', '三': '3', '四': '4',
                '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}


def cn_num_to_arabic(cn_num):
    """将中文数字转换为阿拉伯数字（如 二零二五 -> 2025）"""
    result = ''
    for ch in cn_num:
        if ch in CN_DIGIT_MAP:
            result += CN_DIGIT_MAP[ch]
    if not result:
        return None
    try:
        val = int(result)
        # 处理"十二"->12, "二十"->20 等十位数
        if '十' in cn_num:
            val = 0
            for i, ch in enumerate(cn_num):
                if ch == '十':
                    if i == 0:
                        val = 10
                    else:
                        prev_digit = CN_DIGIT_MAP.get(cn_num[i-1], '0')
                        if prev_digit == '0':
                            val = 10
                        else:
                            val = int(prev_digit) * 10
                elif ch in CN_DIGIT_MAP:
                    val += int(CN_DIGIT_MAP[ch])
        return val
    except:
        return None


def search_stock(keyword, max_num=10):
    data = {'keyWord': keyword, 'maxNum': max_num}
    resp = requests.post(SEARCH_URL, data=data, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()
    if result and len(result) > 0:
        stock_info = result[0]
        print(f"成功获取股票信息: {stock_info.get('zwjc', '')} ({stock_info.get('code', '')})")
        return stock_info
    print(f"未找到股票代码 {keyword} 的信息")
    return None


def get_plate(stock_code, org_id, sjsts_bond):
    url = f"{PLATE_URL}?stockCode={stock_code}&orgId={org_id}&sjstsBond={sjsts_bond}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    match = re.search(r'var\s+plate\s*=\s*["\']([^"\']+)["\'];', resp.text)
    if match:
        print(f"成功获取板块信息: {match.group(1)}")
        return match.group(1)
    return None


def get_plate_param(plate):
    if plate == 'szse':   return 'sz'
    elif plate == 'sse':  return 'sh'
    elif plate == 'bj':   return 'bj;third'
    elif plate == 'hke':  return 'hke'
    return plate


def is_hke_stock(plate):
    """判断是否为港股"""
    return plate == 'hke'


def clean_title(title):
    return re.sub(r'<[^>]+>', '', title)


def extract_year_from_title_hke(title, report_type):
    """
    从港股标题提取报表年度
    港股年报: "截至二零二五年十二月三十一日止年度全年业绩公布"
    港股半年报: "截至二零二五年六月三十日止三个月及六个月业绩公布"
    港股一季报: "截至二零二五年三月三十一日止三个月业绩公布"
    港股三季报: "截至二零二五年九月三十日止三个月及九个月业绩公布"
    """
    t = clean_title(title)

    def get_year_from_cn():
        # 匹配中文数字年份
        match = re.search(r'((?:[零一二三四五六七八九]+))年', t)
        if match:
            return cn_num_to_arabic(match.group(1))
        return None

    if report_type == 'annual':
        if '全年业绩公布' in t or ('全年业绩' in t and '个月' not in t):
            return get_year_from_cn()
    elif report_type == 'half':
        if '六个月业绩' in t:
            return get_year_from_cn()
    elif report_type == 'q1':
        if '三个月业绩' in t and '九个月' not in t:
            return get_year_from_cn()
    elif report_type == 'q3':
        if '九个月业绩' in t:
            return get_year_from_cn()
    return None


def is_annual_report(title):
    """判断是否为年报（不是半年报/季报）"""
    t = clean_title(title)
    # A股: 包含"年度报告"但不是"半年度报告"
    if '年度报告' in t:
        if '半年度' in t:
            return False
        return True
    # 港股: "X 年报" 格式（如"2024 年报"）
    if '年报' in t and '半年度' not in t and '季报' not in t:
        return True
    # 港股: "全年业绩公布" 格式
    if '全年业绩公布' in t:
        return True
    return False


def is_half_report(title):
    """判断是否为半年报"""
    t = clean_title(title)
    # A股: "半年度报告"
    if '半年度' in t and '报告' in t:
        return True
    # 港股: "六个月业绩公布"
    if '六个月业绩' in t:
        return True
    return False


def is_q1_report(title):
    """判断是否为一季报"""
    t = clean_title(title)
    # A股: "第一季度报告" 或 "一季报"
    if ('第一季' in t or '一季' in t) and '报告' in t:
        return True
    # 港股: "三个月业绩公布"（不含"九个月"）
    if '三个月业绩' in t and '九个月' not in t:
        return True
    return False


def is_q3_report(title):
    """判断是否为三季报"""
    t = clean_title(title)
    # A股: "第三季度报告" 或 "三季报"
    if ('第三季' in t or '三季' in t) and '报告' in t:
        return True
    # 港股: "九个月业绩公布"
    if '九个月业绩' in t:
        return True
    return False


def filter_announcements(announcements, report_type, year=None, plate='sse'):
    """
    根据报告类型和年份过滤公告

    Args:
        announcements: 公告列表
        report_type: 报告类型 (annual/half/q1/q3)
        year: 年份过滤，为None时不过滤
        plate: 板块代码，港股需要特殊处理年份提取
    """
    filtered = []
    for ann in announcements:
        title = ann.get('announcementTitle', '')

        if report_type == 'annual' and is_annual_report(title):
            pass
        elif report_type == 'half' and is_half_report(title):
            pass
        elif report_type == 'q1' and is_q1_report(title):
            pass
        elif report_type == 'q3' and is_q3_report(title):
            pass
        else:
            continue

        # 年份过滤
        if year:
            if is_hke_stock(plate):
                report_year = extract_year_from_title_hke(title, report_type)
            else:
                # A股: 从标题提取年份
                t = clean_title(title)
                match = re.search(r'(\d{4})年', t)
                report_year = match.group(1) if match else None

            if report_year and str(report_year) != str(year):
                continue

        filtered.append(ann)
    return filtered


def fetch_announcements(stock_code, org_id, plate, searchkey, page_size=50):
    """获取公告列表"""
    plate_param = get_plate_param(plate)
    announcements = []
    page_num = 1

    while True:
        data = {
            'stock': f"{stock_code},{org_id}",
            'tabName': 'fulltext',
            'pageSize': page_size,
            'pageNum': page_num,
            'column': plate,
            'category': '',
            'plate': plate_param,
            'seDate': '',
            'searchkey': searchkey,
            'secid': '',
            'sortName': '',
            'sortType': '',
            'isHLtitle': 'true'
        }
        resp = requests.post(ANNOUNCEMENT_URL, data=data, headers=HEADERS)
        resp.raise_for_status()
        result = resp.json()

        items = result.get('announcements') or []
        if not items:
            break
        print(f"第{page_num}页获取到 {len(items)} 条公告")
        announcements.extend(items)

        if not result.get('hasMore', False):
            break
        page_num += 1

    return announcements


def download_file(url, file_path, expected_size_kb, max_retries=3):
    attempt = 0
    while attempt < max_retries:
        if attempt > 0:
            time.sleep(1)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(resp.content)
            actual_size = os.path.getsize(file_path) // 1024
            if actual_size >= expected_size_kb - 10:
                print(f"下载成功: {os.path.basename(file_path)} ({actual_size}KB)")
                return True
            print(f"文件大小不匹配: 期望{expected_size_kb}KB, 实际{actual_size}KB")
            attempt += 1
        except Exception as e:
            print(f"下载错误: {e}")
            attempt += 1
    print(f"下载失败，已重试{max_retries}次")
    return False


def extract_date_from_url(adjunct_url):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', adjunct_url)
    return match.group(1) if match else ""


def generate_filename(announcement, date_str):
    sec_code = announcement.get('secCode', '')
    sec_name = announcement.get('secName', '')
    title = clean_title(announcement.get('announcementTitle', ''))
    parts = []
    if date_str:
        parts.append(date_str)
    if sec_code and sec_code not in title:
        parts.append(sec_code)
    if sec_name and sec_name not in title:
        parts.append(sec_name)
    clean_t = re.sub(r'[<>:"/\\|?*]', '_', title)
    parts.append(clean_t)
    return '_'.join(parts) + '.pdf'


def download_reports(stock_code, org_id, plate, category_name, searchkey, save_dir, report_type, year=None, fallback_searchkey=None):
    """
    下载报告
    
    Args:
        fallback_searchkey: 备用搜索关键词，当主搜索无结果时使用（港股年报用）
    """
    announcements = fetch_announcements(stock_code, org_id, plate, searchkey)
    
    # 如果没有找到且设置了备用关键词，尝试备用搜索
    if not announcements and fallback_searchkey:
        print(f"  主搜索无结果，尝试备用搜索: {fallback_searchkey}")
        announcements = fetch_announcements(stock_code, org_id, plate, fallback_searchkey)
    
    if not announcements:
        print(f"  未找到匹配的{category_name}")
        return 0

    # 客户端过滤
    filtered = filter_announcements(announcements, report_type, year=year, plate=plate)
    print(f"  过滤后剩余 {len(filtered)} 条{category_name}")
    if not filtered:
        return 0

    downloaded = 0
    for ann in filtered:
        adjunct_url = ann.get('adjunctUrl', '')
        if not adjunct_url:
            continue
        full_url = FILE_BASE_URL + adjunct_url
        date_str = extract_date_from_url(adjunct_url)
        filename = generate_filename(ann, date_str)
        file_path = os.path.join(save_dir, category_name, filename)
        expected_size = ann.get('adjunctSize', 0) // 1024

        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path) // 1024
            if actual_size >= expected_size - 10:
                print(f"文件已存在且完整，跳过: {filename}")
                continue

        print(f"开始下载: {filename}")
        if download_file(full_url, file_path, expected_size):
            downloaded += 1
            time.sleep(1)
    return downloaded


def main():
    if len(sys.argv) < 2:
        print("使用方法: python download_annual_report.py <股票代码> [分类名] [年份] [保存目录]")
        print("示例: python download_annual_report.py 600519 年报 2024")
        print("       python download_annual_report.py 00700 年报 2025  # 港股")
        return

    stock_code = sys.argv[1]
    category_filter = sys.argv[2] if len(sys.argv) > 2 else '年报'
    year = None
    save_dir = "./downloads"

    # 解析参数
    if len(sys.argv) > 3:
        arg3 = sys.argv[3]
        if arg3.isdigit() and len(arg3) == 4:
            year = arg3
            save_dir = sys.argv[4] if len(sys.argv) > 4 else "./downloads"
        else:
            save_dir = arg3
    if len(sys.argv) > 4:
        save_dir = sys.argv[4]

    if not year:
        year = str(datetime.datetime.now().year)
        print(f"未指定年份，使用当前年份: {year}")

    print("=" * 50)
    stock_info = search_stock(stock_code)
    if not stock_info:
        return

    plate = get_plate(stock_info['code'], stock_info['orgId'], stock_info['sjstsBond'])
    if not plate:
        return

    # 判断是否为港股
    hke = is_hke_stock(plate)

    # 确定要下载的分类
    if category_filter == '全部':
        categories = list(CATEGORY_CONFIG.items())
    else:
        config = CATEGORY_CONFIG.get(category_filter)
        if config:
            categories = [(category_filter, config)]
        else:
            categories = [(category_filter, (category_filter, category_filter, category_filter, 'annual'))]

    # 创建保存目录
    stock_name = stock_info['zwjc']
    stock_save_dir = os.path.join(save_dir, stock_name)
    os.makedirs(stock_save_dir, exist_ok=True)

    total_downloaded = 0
    for cat_name, config in categories:
        dir_name, a_share_searchkey_template, hke_searchkey, report_type = config

        # 港股和A股使用不同的搜索关键词
        fallback_searchkey = None
        if hke:
            # 港股searchkey可能是元组(优先,备用)或字符串
            if isinstance(hke_searchkey, tuple):
                searchkey = hke_searchkey[0]
                fallback_searchkey = hke_searchkey[1]
                print(f"  [港股优先搜索: {searchkey}, 备用: {fallback_searchkey}]")
            else:
                searchkey = hke_searchkey
            if year:
                print(f"  [港股使用客户端年份过滤]")
        else:
            searchkey = a_share_searchkey_template.format(year=year)

        print(f"\n处理分类: {cat_name} (搜索: {searchkey})")
        print("-" * 30)

        downloaded = download_reports(
            stock_info['code'], stock_info['orgId'], plate,
            dir_name, searchkey, stock_save_dir, report_type, year=year,
            fallback_searchkey=fallback_searchkey
        )
        print(f"分类 {cat_name} 下载完成: {downloaded} 个文件")
        total_downloaded += downloaded

    print("\n" + "=" * 50)
    print(f"下载完成! 总共下载 {total_downloaded} 个文件")
    print(f"文件保存在: {stock_save_dir}")


if __name__ == "__main__":
    main()