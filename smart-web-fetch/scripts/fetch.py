#!/usr/bin/env python3
"""
Smart Web Fetch - 完整的智能网页获取工具
自动转换 URL + 获取清洗后的 Markdown 内容
"""

import sys
import urllib.parse
import urllib.request
import ssl
import json

# 忽略 SSL 验证
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def is_captcha_page(content: str) -> bool:
    """检测是否为验证码/异常页面，是则跳过"""
    captcha_keywords = [
        '验证码', '请先验证', 'captcha', '异常', '安全验证',
        '请求异常', '稍后重试', '频繁', '请刷新重试',
        '当前请求异常', '非法请求'
    ]
    content_lower = content.lower()
    for kw in captcha_keywords:
        if kw in content or kw.lower() in content_lower:
            return True
    # 短内容 + 无标题 = 大概率是错误页
    if len(content.strip()) < 200 and '##' not in content:
        return True
    return False


def get_clean_content(url: str, timeout: int = 30) -> dict:
    """
    获取网页的干净 Markdown 内容
    策略: Jina → markdown.new → defuddle.md → 原始内容
    
    Returns:
        {
            "success": bool,
            "url": str,           # 实际使用的清洗服务 URL
            "content": str,       # 获取到的内容
            "source": str,        # 使用的服务: jina/markdown-new/defuddle/original
            "error": str          # 失败时的错误信息
        }
    """
    original_url = url.strip()
    
    # 清洗服务列表（按优先级）
    services = [
        ("jina", lambda u: f"https://r.jina.ai/http://{u.replace('https://', '').replace('http://', '')}"),
        ("markdown-new", lambda u: f"https://markdown.new/{u}"),
        ("defuddle", lambda u: f"https://defuddle.md/{u}"),
    ]
    
    # 尝试每个服务
    for service_name, url_builder in services:
        try:
            clean_url = url_builder(original_url)
            result = fetch_url(clean_url, timeout)
            
            if result["success"] and len(result["content"]) > 100:
                # 检测是否为验证码/异常页面，是则跳过尝试下一个服务
                if is_captcha_page(result["content"]):
                    continue
                return {
                    "success": True,
                    "url": clean_url,
                    "content": result["content"],
                    "source": service_name,
                    "error": None
                }
        except Exception as e:
            continue
    
    # 所有清洗服务都失败，尝试直接获取原始内容
    try:
        result = fetch_url(original_url, timeout)
        if result["success"] and result["content"]:
            if is_captcha_page(result["content"]):
                return {
                    "success": False,
                    "url": original_url,
                    "content": "",
                    "source": "none",
                    "error": "All services returned CAPTCHA or error pages"
                }
            return {
                "success": True,
                "url": original_url,
                "content": result["content"],
                "source": "original",
                "error": None
            }
    except Exception as e:
        pass
    
    return {
        "success": False,
        "url": original_url,
        "content": "",
        "source": "none",
        "error": "All services failed to fetch content"
    }


def fetch_url(url: str, timeout: int = 30) -> dict:
    """获取 URL 内容"""
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
    )
    
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
        content = response.read().decode('utf-8', errors='ignore')
        return {
            "success": response.status == 200,
            "content": content,
            "status": response.status
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch.py <url> [--json]", file=sys.stderr)
        print("  --json    Output as JSON", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    output_json = "--json" in sys.argv
    
    result = get_clean_content(url)
    
    if output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["success"]:
            print(f"# Source: {result['source']}")
            print(f"# URL: {result['url']}")
            print()
            print(result["content"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
