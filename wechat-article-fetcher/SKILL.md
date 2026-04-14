---
name: wechat-article-fetcher
description: 微信公众号文章抓取和备份工具。当提到「抓取微信文章、备份公众号文章、保存文章到本地、下载微信文章、添加到CSV列表、批量下载公众号」时触发。支持从CSV批量抓取文章、下载图片、转换为Markdown/HTML格式，添加新文章链接到CSV列表。用于微信公众号文章备份和归档。注意：本Skill只处理文件备份，不做知识提炼（那是llm-wiki的工作）。
---

# 微信公众号文章抓取工具

**⚠️ 关键检查点：** 执行任何抓取操作前，先确认 OUTPUT_DIR 环境变量已配置且路径可写。

---

## ⚠️ 本 Skill 的边界（重要）

**本 Skill 处理的是：技术层面的「文件备份」**
- 把微信文章下载为 `.md` / `.html` 文件到本地
- 存储到 Git 仓库备份
- 不做任何知识提炼、分析、存入维基的操作

**走本 Skill 的指令特征：**
- "抓取微信文章"
- "备份公众号文章"
- "保存文章到本地"
- "下载微信文章"
- "把链接里的文章下载下来"
- "添加到 CSV 列表"
- "批量下载公众号"

**❌ 不要走本 Skill（走 llm-wiki）：**
- "存到个人维基" / "存入 wiki" / "整理到知识库"
- "提炼文章要点" / "分析这篇文章"
- "帮我消化这篇文章"
- "做个摘要"

**关键区分：**
| 需求 | Skill |
|------|-------|
| 要文件（下载备份） | wechat-article-fetcher |
| 要知识（提炼存入） | llm-wiki |

---

## 功能概述：

本 Skill 提供微信公众号文章的完整抓取和备份解决方案：

1. **批量抓取文章** (`fetch_weixin_articles.py`): 从CSV列表批量抓取文章，保存为Markdown和HTML格式，自动下载图片
2. **添加新文章** (`add_article.py`): 解析单个文章链接，自动提取标题和发布时间，添加到CSV列表

## 工作流程

### 1. 添加新文章到列表

当用户需要添加新的公众号文章链接时：

**Step 1. 检查环境**
- 确认 `.env` 文件中 `OUTPUT_DIR` 已配置
- 确认 `ARTICLES_CSV_FILE` 指向正确路径

**Step 2. 执行添加**
```python
# 使用 add_article.py 脚本
python add_article.py "https://mp.weixin.qq.com/s/xxxxx"
```

脚本会自动：
- 抓取文章页面提取标题和发布时间
- 分配新序号（当前最大序号 + 1）
- 插入到CSV文件开头
- 检测重复链接

**Step 3. 确认结果**
- 报告新添加的文章信息（序号、标题、发布时间）
- 如添加失败，说明原因并建议解决方案

### 2. 批量抓取文章

当用户需要从CSV批量下载文章时：

**Step 1. 确认环境**
- 确认 `.env` 文件中 `OUTPUT_DIR` 配置正确
- 确认 `ARTICLES_CSV_FILE` 指向正确的CSV文件
- 确认CSV文件存在且有内容
- 确认OUTPUT_DIR路径可写

**Step 2. 告知用户并确认**
- 告知用户预计抓取数量
- 请用户确认是否开始

**Step 3. 执行抓取**
```python
# 使用 fetch_weixin_articles.py 脚本
python fetch_weixin_articles.py
```

脚本会：
- 读取CSV文件获取文章列表
- 逐个抓取文章内容
- 下载图片并替换链接
- 保存为Markdown和HTML格式
- 支持断点续传

**Step 4. 监控进度**
- 每个文章抓取后报告进度（序号/标题/状态）
- 失败文章记录到日志，提供重试方案

**Step 5. 完成报告**
- 报告成功/失败数量
- 列出失败的文章及原因
- 提示查看日志文件获取详细信息

```
wechat_articles_downloads/
├── articles_with_publish_date.csv  # 文章列表（序号,文章名,发布时间,URL）
├── fetch_weixin_articles.py        # 批量抓取脚本
├── add_article.py                  # 添加单篇文章脚本
├── .env                            # 环境变量配置
├── progress.json                   # 抓取进度（自动生成）
└── fetch.log                       # 日志文件（自动生成）
```

## CSV格式

```csv
序号,文章名,发布时间,URL
439,文章标题,2026-03-28,https://mp.weixin.qq.com/s/xxxxx
```

- 序号：文章唯一ID，倒序排列（新文章序号更大）
- 文章名：文章标题
- 发布时间：格式 YYYY-MM-DD
- URL：微信文章链接

## 环境变量配置

创建 `.env` 文件：

```ini
# 必需：输出目录
OUTPUT_DIR=C:/Users/username/Desktop/wechat_articles

# 可选：CSV文件路径
ARTICLES_CSV_FILE=./articles_with_publish_date.csv

# 可选：请求间隔（防封）
MIN_DELAY=1
MAX_DELAY=2
IMG_MIN_DELAY=0.5
IMG_MAX_DELAY=1.5

# 可选：重试次数
MAX_RETRIES=3
```

## 输出目录结构

```
OUTPUT_DIR/
├── html_source/          # HTML缓存（断点续传用）
├── html/                 # 提取后的HTML（阅读用）
├── md/                   # Markdown文件
└── images/               # 下载的图片
    └── 2026-03-28_文章标题/
        ├── img_000.jpg
        └── ...
```

## 依赖安装

```bash
pip install requests beautifulsoup4 urllib3 python-dotenv
```

## 脚本使用指南

### add_article.py

**功能**: 添加单篇文章到CSV列表

**用法**:
```bash
# 命令行传参
python add_article.py "https://mp.weixin.qq.com/s/xxxxx"

# 交互模式
python add_article.py
```

**流程**:
1. 输入微信文章链接
2. 自动抓取文章标题和发布时间
3. 如果无法识别发布时间，提示手动输入
4. 新文章以新序号插入CSV开头
5. 序号是固定ID，不会重新编排

### fetch_weixin_articles.py

**功能**: 批量抓取CSV中的所有文章

**用法**:
```bash
# 直接运行
python fetch_weixin_articles.py
```

**特性**:
- 自动创建输出目录
- 支持断点续传（通过 progress.json）
- 防封机制：随机延时、User-Agent轮换
- 自动下载图片并替换链接
- 生成Markdown和HTML两种格式

**断点续传**:
- 中断后重新运行会从上次位置继续
- 如需重新抓取，删除 progress.json

## 注意事项

1. **序号是固定ID**：不要重新编号，否则缓存HTML和序号无法对应
2. **防封机制**：设置了随机延时，请耐心等待
3. **图片下载**：会自动下载文章中的图片到本地
4. **链接失效**：部分旧文章可能已被删除，会记录到失败列表

## 异常处理

| 异常情况 | 处理方式 |
|----------|----------|
| 链接已失效（404/被删除） | 记录到失败列表，跳过抓取下一个 |
| 网络超时 | 自动重试（最多3次），仍失败则跳过 |
| 磁盘空间不足 | 停止抓取，提示清理空间 |
| CSV文件不存在 | 提示检查 ARTICLES_CSV_FILE 配置 |
| 环境变量未配置 | 提示配置 OUTPUT_DIR 和 ARTICLES_CSV_FILE |
| 图片下载失败 | 继续抓取文章，图片链接保留原样 |
| CSV文件为空 | 提示CSV没有内容，无需抓取 |
| 路径包含空格或中文 | 脚本会自动处理，无需用户干预 |
| 重复抓取同一文章 | 跳过已抓取的文章（根据序号判断） |
| User-Agent被封禁 | 降低请求频率，延长MIN_DELAY/MAX_DELAY |

## 参考代码

详细实现代码见 `scripts/` 目录：
- `scripts/fetch_weixin_articles.py` - 批量抓取完整实现
- `scripts/add_article.py` - 添加文章完整实现
