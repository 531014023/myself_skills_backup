---
name: cninfo-annual-download
description: 巨潮资讯网年报下载器 - 支持A股（沪/深/北交所）和港股的年报、半年报、季报等定期报告下载，按股票代码、年份、分类精确筛选
trigger: "下载.*年报|巨潮.*公告|cninfo|巨潮资讯|.*年.*报.*下载"
---

# 巨潮资讯网年报下载技能

## 描述

用于下载巨潮资讯网（cninfo.com.cn）上市公司年报、半年报、季报等定期报告的技能。支持按股票代码获取板块信息、公告分类，并下载PDF文件到本地。**支持A股（沪/深/北交所）和港股**，港股使用中文数字年份过滤（如二零二五→2025）。

## 使用场景

当用户提出以下需求时触发此技能：
- 下载某股票的年报/半年报/季报
- 下载巨潮资讯网的公告文件
- 批量下载某公司的历史公告
- 获取上市公司的定期报告
- 下载港股（如腾讯）的年报

## 核心接口

### 1. 股票搜索接口
- **URL**: `POST https://www.cninfo.com.cn/new/information/topSearch/query`
- **参数**: `keyWord` (股票代码), `maxNum` (最大返回数)
- **返回**: 股票基本信息，包含 `code`, `orgId`, `sjstsBond`, `zwjc` 等字段

### 2. 板块信息获取
- **URL**: `GET https://www.cninfo.com.cn/new/disclosure/stock?stockCode={code}&orgId={orgId}&sjstsBond={sjstsBond}`
- **解析**: 从返回HTML中提取 `var plate = "xxx";` 变量
- **板块代码**: `sse` (上交所), `szse` (深交所), `bj` (北交所), `hke` (港交所)

### 3. 公告查询接口
- **URL**: `POST https://www.cninfo.com.cn/new/hisAnnouncement/query`
- **参数**:
  - `stock`: `{股票代码},{orgId}`
  - `column`: 板块代码 (sse/szse/bj/hke)
  - `plate`: 板块参数 (sh/sz/bj;third/hke)
  - `pageSize`: 每页数量
  - `pageNum`: 页码
  - `searchkey`: 搜索关键词

### 4. 文件下载
- **URL**: `https://static.cninfo.com.cn/` + `adjunctUrl`
- **方法**: requests
- **文件名格式**: `{日期}_{股票代码}_{股票名称}_{标题}.pdf`

## 公告标题格式

### A股（沪深北交所）
- 年报: `贵州茅台2024年年度报告`
- 半年报: `贵州茅台2024年半年度报告`
- 一季报: `贵州茅台2024年第一季度报告`
- 三季报: `贵州茅台2024年第三季度报告`

### 港股
- 年报: `截至二零二五年十二月三十一日止年度全年业绩公布`
- 半年报: `截至二零二五年六月三十日止三个月及六个月业绩公布`
- 一季报: `截至二零二五年三月三十一日止三个月业绩公布`
- 三季报: `截至二零二五年九月三十日止三个月及九个月业绩公布`

## 使用命令

```bash
# 下载A股某股票的年报
python scripts/download_annual_report.py <股票代码> [分类名] [年份] [保存目录]

# 示例：下载贵州茅台2024年年报
python scripts/download_annual_report.py 600519 年报 2024

# 示例：下载腾讯控股2025年年报（港股）
python scripts/download_annual_report.py 00700 年报 2025

# 示例：下载历年所有年报
python scripts/download_annual_report.py 600519 年报

# 示例：下载指定年份半年报
python scripts/download_annual_report.py 600519 半年报 2024
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| 第1个参数 | 股票代码（必填） | `600519`、`00700` |
| 第2个参数 | 分类名（可选，默认年报） | `年报`、`半年报`、`一季报`、`三季报`、`全部` |
| 第3个参数 | 年份（可选，4位数字，如2024；港股支持中文数字年份自动转换） | `2024`、`2025` |
| 第4个参数 | 保存目录（可选） | `./downloads` |

## 配置文件

- `references/list-search.json`: 包含各板块的公告分类定义

## 脚本资源

- `scripts/download_annual_report.py`: 年报下载核心脚本
- 支持命令行参数: 股票代码、分类过滤、年份过滤

## 依赖

```
requests>=2.31.0
beautifulsoup4>=4.12.2
lxml>=4.9.3
```