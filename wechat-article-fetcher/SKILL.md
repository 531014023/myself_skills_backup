---
name: wechat-article-fetcher
description: 微信公众号文章抓取和备份工具。当提到「抓取微信文章、备份公众号文章、保存文章到本地、下载微信文章、添加到CSV列表、批量下载公众号」时触发。支持从CSV批量抓取文章、下载图片、转换为Markdown/HTML格式，添加新文章链接到CSV列表。用于微信公众号文章备份和归档。注意：本Skill只处理文件备份，不做知识提炼（那是llm-wiki的工作）。
---

# 微信公众号文章抓取工具

## 边界声明

**必须先满足以下条件，才执行本 Skill 的流程。**

### 1. 本 Skill 处理的是什么？

**技术层面的「文件备份」：**
- 把微信文章下载为 `.md` / `.html` 文件到本地
- 存储到 Git 仓库备份
- 不做任何知识提炼、分析、存入维基的操作

### 2. 走本 Skill 的指令特征

- "抓取微信文章"
- "备份公众号文章"
- "保存文章到本地"
- "下载微信文章"
- "把链接里的文章下载下来"
- "添加到 CSV 列表"
- "批量下载公众号"

### 3. 不要走本 Skill（走 llm-wiki）

| 需求 | Skill |
|------|-------|
| "存到个人维基" / "存入 wiki" / "整理到知识库" | llm-wiki |
| "提炼文章要点" / "分析这篇文章" | llm-wiki |
| "帮我消化这篇文章" | llm-wiki |
| "做个摘要" | llm-wiki |

### 4. 关键区分

| 需求类型 | Skill |
|---------|-------|
| 要文件（下载备份） | wechat-article-fetcher |
| 要知识（提炼存入） | llm-wiki |

### 5. 判断流程

```
用户输入 → 是否涉及微信文章备份？
  ├── 否 → 不触发本 Skill
  └── 是 → 备份范围是文件还是知识？
              ├── 只要文件备份 → wechat-article-fetcher ✓
              └── 需要知识提炼 → llm-wiki（可能需要两者配合）
```

**⚠️ 如果不满足本 Skill 的边界条件，应重新评估是否需要触发其他 Skill（如 llm-wiki）。**

---

## 初始化

**每次执行 Skill 前必须先完成初始化：**

**Step 1. 读取 skill .env**
- 读取 `~/.agents/skills/wechat-article-fetcher/.env`
- 提取 `PROJECT_DIR`，设置环境变量

**Step 2. 读取项目 .env 并设置环境变量**
- 读取 `$env:PROJECT_DIR/.env`
- 遍历每一行配置，解析键值对
- 如果值是相对路径（如 `./articles_with_publish_date.csv`），拼接成绝对路径后设置环境变量
- 其他配置直接设置环境变量
- **验证关键配置**：确保解析到 `ARTICLE_CSV_FILE` 和 `OUTPUT_DIR`
  - 如果缺失其中任一项，**停止执行**，提示用户检查项目 `.env` 配置

**Step 3. 切换目录**
- `cd $env:PROJECT_DIR`
- 后续所有操作在项目根目录下执行

**环境变量汇总：**

| 变量 | 来源 | 示例值 |
|------|------|--------|
| `PROJECT_DIR` | skill .env | `C:\Users\53101\Desktop\project\codebuddy\work\wechat_articles_downloads` |
| `ARTICLE_CSV_FILE` | 拼接（绝对路径） | `C:\Users\53101\Desktop\project\codebuddy\work\wechat_articles_downloads\articles_with_publish_date.csv` |
| `OUTPUT_DIR` | 拼接（绝对路径） | `C:\Users\53101\Desktop\project\codebuddy\work\wechat_articles_downloads\backup` |

---

## 完整备份流程（4 步）

```
1. 添加文章到 CSV        → Step 1
2. 抓取文章              → Step 2
3. Git 提交推送          → Step 3
4. 上传到 IMA 知识库     → Step 4
```

---

## Step 1: 添加文章到 CSV

**Step 1.1 执行添加**
```powershell
cd $PROJECT_DIR
python add_article.py "https://mp.weixin.qq.com/s/xxxxx"
```

脚本会自动：
- 抓取文章页面提取标题和发布时间
- 分配新序号（当前最大序号 + 1）
- 插入到 CSV 文件开头
- 检测重复链接

**Step 1.2 确认结果**
- 报告新添加的文章信息（序号、标题、发布时间）
- 如添加失败，说明原因并建议解决方案

---

## Step 2: 批量抓取文章

**Step 2.1 执行抓取**
```powershell
cd $PROJECT_DIR
python fetch_weixin_articles.py
```

脚本会：
- 读取 CSV 文件获取文章列表
- 逐个抓取文章内容
- 下载图片并替换链接
- 保存为 Markdown 和 HTML 格式
- 支持断点续传

**Step 2.2 监控进度**
- 每个文章抓取后报告进度（序号/标题/状态）
- 失败文章记录到日志，提供重试方案

**Step 2.3 完成报告**
- 报告成功/失败数量
- 列出失败的文章及原因
- 提示查看日志文件获取详细信息

---

## Step 3: Git 提交推送

**Step 3.1 执行 Git 命令**
```powershell
cd $PROJECT_DIR
git add .
git commit -m "feat: 添加微信文章 $(Get-Date -Format 'yyyy-MM-dd')"
git push
```

**Step 3.2 确认推送成功**
- 报告提交 hash 和推送状态

---

## Step 4: 上传到 IMA 知识库

**Step 4.1 准备环境变量**

在调用脚本前，设置文章关键字：
```powershell
$env:ARTICLE_KEYWORD = "文章标题关键字"
```

**Step 4.2 执行上传**

使用项目目录`PROJECT_DIR`下的ima上传脚本 `ima_upload.py`
```powershell
cd $PROJECT_DIR
$env:ARTICLE_KEYWORD = "文章标题关键字"
python ima_upload.py
```

### IMA 上传流程说明

脚本执行时会自动完成以下步骤：

1. **读取 CSV**：获取最新文章的公众号名
2. **获取 KB_ID**：调用 IMA API 列出知识库，匹配公众号名
3. **获取 folder_id**：调用 IMA API 列出文件夹，找到 `md/` 文件夹
4. **查找文件**：在 `backup/{公众号名}/md/` 下匹配文章关键字
5. **上传文件**：create_media → cos-upload → add_knowledge

### 各步骤文件名规则

| 步骤 | 文件名 | 文件路径 |
|------|--------|----------|
| create_media | ✅ 正确的目标文件名 | - |
| cos-upload | - | ✅ 临时文件路径 |
| add_knowledge | ✅ 正确的目标文件名 | - |

### ⚠️ IMA 无删除接口
- 上传到错误位置须手动在 IMA 界面删除

### IMA API 响应说明
- 返回字段是 `code`，不是 `retcode`
- 成功：`code: 0`，失败：`code: 非0`，错误信息在 `msg` 字段

---

## md 文件正确路径

**动态路径**（根据公众号名自动拼接）：
```
PROJECT_DIR/backup/{公众号名}/md/
```

示例：
- 太阳照常升起：`PROJECT_DIR/backup/太阳照常升起/md/`
- 另一个公众号：`PROJECT_DIR/backup/另一个公众号/md/`

---

## CSV 格式

```csv
序号,文章名,发布时间,公众号,URL
466,欧洲忘记了凯恩斯,2026-04-15,太阳照常升起,https://mp.weixin.qq.com/s/xxxxx
```

- 序号：文章唯一 ID，倒序排列（新文章序号更大）
- 文章名：文章标题
- 发布时间：格式 YYYY-MM-DD
- 公众号：公众号名称（由 add_article.py 自动提取）
- URL：微信文章链接

---

## 输出目录结构

```
PROJECT_DIR/
├── .env                    # 项目配置（OUTPUT_DIR、CSV路径、防封延时等）
├── articles_with_publish_date.csv
├── fetch_weixin_articles.py
├── add_article.py
├── progress.json           # 抓取进度（自动生成）
├── fetch.log               # 日志文件（自动生成）
└── backup/
    └── 太阳照常升起/
        ├── html_source/    # HTML缓存（断点续传用）
        ├── html/           # 提取后的HTML（阅读用）
        ├── md/             # Markdown文件
        └── images/         # 下载的图片
            └── YYYY-MM-DD_文章标题/
                ├── img_000.jpg
                └── ...
```

---

## 异常处理

| 异常情况 | 处理方式 |
|----------|----------|
| 链接已失效（404/被删除） | 记录到失败列表，跳过抓取下一个 |
| 网络超时 | 自动重试（最多3次），仍失败则跳过 |
| 磁盘空间不足 | 停止抓取，提示清理空间 |
| CSV文件不存在 | 提示检查 ARTICLE_CSV_FILE 配置 |
| 环境变量未配置 | 提示配置 OUTPUT_DIR 和 ARTICLE_CSV_FILE |
| 图片下载失败 | 继续抓取文章，图片链接保留原样 |
| CSV文件为空 | 提示CSV没有内容，无需抓取 |
| 路径包含空格或中文 | 脚本会自动处理，无需用户干预 |
| 重复抓取同一文章 | 跳过已抓取的文章（根据序号判断） |
| User-Agent被封禁 | 降低请求频率，延长MIN_DELAY/MAX_DELAY |
| IMA 上传失败 | 报告错误信息，检查知识库是否存在 md/ 文件夹 |
| IMA 知识库未匹配 | 确保知识库名称包含公众号名，或公众号名称正确 |

---

## 脚本使用指南

### add_article.py

**功能**：添加单篇文章到 CSV 列表

**用法**：
```bash
cd $PROJECT_DIR
python add_article.py "https://mp.weixin.qq.com/s/xxxxx"
```

**流程**：
1. 输入微信文章链接
2. 自动抓取文章标题和发布时间
3. 如果无法识别发布时间，提示手动输入
4. 新文章以新序号插入 CSV 开头
5. 序号是固定 ID，不会重新编排

### fetch_weixin_articles.py

**功能**：批量抓取 CSV 中的所有文章

**用法**：
```bash
cd $PROJECT_DIR
python fetch_weixin_articles.py
```

**特性**：
- 自动创建输出目录
- 支持断点续传（通过 progress.json）
- 防封机制：随机延时、User-Agent轮换
- 自动下载图片并替换链接
- 生成 Markdown 和 HTML 两种格式

**断点续传**：
- 中断后重新运行会从上次位置继续
- 如需重新抓取，删除 progress.json

---

## 注意事项

1. **序号是固定ID**：不要重新编号，否则缓存 HTML 和序号无法对应
2. **防封机制**：设置了随机延时，请耐心等待
3. **图片下载**：会自动下载文章中的图片到本地
4. **链接失效**：部分旧文章可能已被删除，会记录到失败列表
5. **IMA 上传**：每次上传前必须设置 `ARTICLE_KEYWORD` 环境变量
7. **IMA 知识库**：确保知识库中存在 `md/` 文件夹，否则上传会失败
8. **多公众号支持**：脚本会自动从 CSV 读取公众号名，无需手动配置
