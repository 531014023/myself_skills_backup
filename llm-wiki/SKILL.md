---
name: llm-wiki
description: 个人知识库、个人wiki、个人维基、个人笔记管理。当提到"个人知识库"、"个人wiki"、"个人维基"、"个人笔记"、"建立wiki"、"整理知识库"时触发。基于 Karpathy LLM Wiki 模式。AI负责知识整合、内联更新、矛盾检测；人类负责素材采集、问题提问、方向探索。三层架构：原始素材 → AI合成Wiki → 行为Schema。
---

# LLM Wiki - 个人知识管理系统

## 核心理念

LLM Wiki 是一种 AI 增强的知识管理范式：AI 不仅回答问题，更承担"簿记"工作——更新交叉引用、标注矛盾、保持一致性。人类聚焦于素材采集、探索提问和方向把控。

**五大原则：**
1. **原始素材不可变** — 永不修改 source 文档，只增不减
2. **LLM 拥有 Wiki** — 用户阅读，LLM 负责写入和维护
3. **知识复利** — 每一次摄入和查询都会丰富 Wiki
4. **富维基** — 把有价值的分析沉淀回 Wiki，不要让好答案消失在聊天里
5. **定期除絮** — 保持 Wiki 健康生长的同时维持其健康状态

## 三层架构

### Layer 1: Raw Sources `~/wiki/sources/`
原始文档，不可变。包括：Web clipping、读书笔记、播客摘要、会议纪要、论文。

```markdown
---
id: 2024-04-12-注意力机制概述
source: https://arxiv.org/abs/1706.03762
date: 2024-04-12
tags: [transformer, attention]
---

# Attention Is All You Need - 摘要
（原始内容一字不改）
```

**文件名：中文**，格式 `YYYY-MM-DD-中文标题.md`

### Layer 2: AI Wiki `~/wiki/wiki/`
AI 综合多个 sources 生成的结构化知识条目。

```markdown
---
title: 注意力机制
created: 2024-03-16
updated: 2024-04-12
tags: [transformer, attention]
confidence: high
sources: [2024-03-16-注意力机制详述, 2024-04-02-transformer论文笔记]
---

# 注意力机制

## 定义
一种让序列中任意位置能获取其他位置信息的技术。

## 关键要点
- **Self-attention**: Query/Key/Value 来自同一序列
- **Multi-head attention**: 多组并行 attention，捕捉不同子特征

## 相关概念
- [[2024-03-10-transformer架构]] — 上层架构
- [[2024-03-15-自注意力]] — 详细对比见自注意力条目

## 来源
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
```

**文件名格式：** `YYYY-MM-DD-标题.md`（用于排序和版本）

### Layer 3: Schema `~/wiki/schema.md`
指导 AI 行为的规则和约定。

```markdown
# LLM Wiki Schema

## 条目格式规范
- 文件名: `YYYY-MM-DD-标题.md`，存放在对应领域目录下
- Frontmatter 必须字段: title, created, updated, confidence, sources

## 链接规范
- Wiki 内部链接: `[[页面名称]]`（使用中文）
- 外部链接: `[描述](url)`

## 质量标准
- confidence: high (有多个 source 交叉验证) | medium | low (单来源或推断)
- 每个 assertion 需有 source 引用
```

## 核心操作

### 1. Ingest — 摄入素材

**触发词：** 提供链接/文件/粘贴内容/文件夹

**输入类型及处理方式：**

| 输入类型 | 处理方式 |
|----------|----------|
| URL | WebFetch/smart-web-fetch 抓取 |
| 粘贴文本 | 直接解析 |
| 文件路径 | 读取并解析 |
| 文件夹路径 | 扫描并批量处理 |

**执行步骤：**

1. **识别输入类型**
   - URL → WebFetch/smart-web-fetch 抓取
   - 文本 → 直接解析
   - 文件夹 → 扫描所有 .md/.txt/.pdf 等文件

2. **解析内容**
   - 提取标题、主要内容、关键术语
   - 记录来源信息（URL、文件名、日期）
   - 文件名格式: `YYYY-MM-DD-中文标题.md`

3. **存储到 sources/**
   - 文件名: `YYYY-MM-DD-中文标题.md`（中文标题来自内容）
   - 添加 YAML frontmatter (id, source, date, tags)

4. **关联 Wiki**
   - 提取核心概念
   - 识别相关已有条目
   - **分析内容主题，确定分类**（成长/研究/读书/业务/学习等）
   - 更新相关条目：添加交叉链接、补充内容

5. **报告**
   - 列出本次影响的所有 Wiki 条目
   - 如有新概念，提示是否创建新条目

**输出示例：**

```
用户: https://arxiv.org/abs/1706.03762
AI:
  → 正在抓取...
  ✓ sources/2024-04-12-注意力机制概述.md 已创建
  识别概念: attention, self-attention, multi-head, positional encoding
  分析分类: 研究/机器学习
  → 更新 wiki/研究/2024-04-12-transformer架构.md
  → 新建 wiki/研究/2024-04-12-注意力机制.md

用户: 这是我整理的文章 [粘贴内容]
AI:
  ✓ sources/2024-04-12-文章笔记.md 已创建
  分析分类: 成长/习惯
  → 关联 wiki/成长/2024-04-12-xxx.md (已更新)

用户: D:\Articles\LLM\
AI:
  → 扫描 12 个文件...
  ✓ 已摄入 12 个文件到 sources/
  分析分类: 研究 (8篇), 学习 (4篇)
  → 影响 5 个 Wiki 条目
```

### 2. Query — 查询知识

**触发词：** 提问

**执行步骤：**

1. **理解问题**
   - 提取关键概念和术语
   - 识别问题类型（事实/解释/分析/建议）

2. **Wiki 优先查询**
   - 在 wiki/ 目录搜索相关条目
   - 综合多个条目内容回答

3. **补充来源**
   - 必要时引用 sources/ 中的原始素材
   - 提供可核查的引用

4. **标注不确定性**
   - confidence 等级 (high/medium/low)
   - 明确知识空白区域

5. **富维基触发**
   - 回答质量高时，提示用户：「这个回答是否需要存到维基？」

### 3. 富维基 — 沉淀好答案

**触发词：** 「存到维基」「这个值得记」「反馈到 wiki」

**判断标准：** 这个回答是否解决了一个以后还会问的问题？

**执行步骤：**

1. 识别本次回答的核心洞察（不同于 sources 的综合结论）
2. 分析内容主题，确定分类
3. 写入 `wiki/[分类]/` 对应条目（如无则新建）
4. 标注 `confidence: high` 并注明「来自 AI 综合」
5. 更新 `sources/` 添加一条 AI 合成笔记引用原对话

**输出示例：**

```
用户: attention mechanism 和 self-attention 的核心区别是什么？
AI: [综合回答，标注 confidence 和来源]

用户: 存到维基
AI: ✓ 已更新 wiki/研究/2024-04-12-注意力机制.md
    新增「self-attention vs attention」对比段
```

### 4. Lint — 维基体检

**触发词：** 「维基体检」「lint」「检查维基」

**执行步骤：**

1. **检查断链**
   - 扫描所有 `[[wikilinks]]`
   - 验证目标文件在 wiki/ 目录存在

2. **发现矛盾**
   - 同一概念在不同条目的说法对比
   - 事实性错误检测
   - 标注矛盾程度（严重/轻微）

3. **识别知识空白**
   - 相关主题缺失检测
   - 过时信息标注（超过 30 天未更新）
   - 孤儿页面检测（无引用链的页面）

4. **输出报告**
   - 问题列表（类型、位置、建议修复）
   - 优先级排序

**执行频率：** 每两周一次，或积累 20+ 新素材后集中 lint。

**输出示例：**

```
两周后，用户: 维基体检
AI:
  ✓ 断链: 无
  ⚠ 矛盾: wiki/研究/注意力机制.md 与 wiki/研究/transformer架构.md
          对「multi-head attention 头数」描述不一致 (8 vs 16)
  ⚠ 孤儿: wiki/学习/强化学习.md 无引用
  ⚠ 过时: 语言模型.md 超过 30 天未更新
  建议: 确认头数；删除或保留强化学习？
```

## 工作流实例

**背景：** 用户阅读了 Transformer 论文，想整理到知识库。

**Step 1: Ingest**
```
用户: https://arxiv.org/abs/1706.03762
AI:
  → 正在抓取...
  ✓ sources/2024-04-12-注意力机制概述.md 已创建
  分析分类: 研究/机器学习
  → 更新 wiki/研究/2024-04-12-transformer架构.md (新增 architecture 概述)
  → 新建 wiki/研究/2024-04-12-注意力机制.md (新增 multi-head attention 要点)

用户: D:\Articles\LLM\  (文件夹)
AI:
  → 扫描 12 个文件...
  ✓ 已摄入 12 个文件，分析分类: 研究 (8篇), 学习 (4篇)
```

**Step 2: Query + 富维基**
```
用户: multi-head attention 的作用是什么？
AI: [从 wiki/研究/2024-04-12-注意力机制.md 综合回答，标注 confidence: high]

用户: 存到维基
AI: ✓ wiki/研究/2024-04-12-注意力机制.md 已更新，新增「multi-head attention 作用」段
```

**Step 3: Lint**
```
两周后，用户: 维基体检
AI:
  ✓ 断链: 无
  ⚠ 矛盾: wiki/研究/注意力机制.md 与 wiki/研究/transformer架构.md
          对「multi-head attention 头数」描述不一致 (8 vs 16)
  ⚠ 孤儿: wiki/学习/强化学习.md 无引用
  建议: 确认头数；删除或保留强化学习？
```

## 适用场景

| 领域 | 原始素材 | Wiki 条目 |
|------|----------|-----------|
| **个人成长** | 日记、文章、播客笔记 | 目标、健康追踪、自我提升 |
| **学术研究** | 论文、文章、报告 | 实体、概念、演进中的 thesis |
| **读书** | 章节笔记 | 人物、主题、情节线索 |
| **业务** | Slack 讨论、会议记录 | 内部知识库 |
| **竞品分析** | 公司报告、新闻 | 竞品画像、对比分析 |
| **课程学习** | 讲座笔记、阅读材料 | 主题摘要、概念图 |

## Obsidian 集成

推荐使用 Obsidian 作为 Wiki 查看器：

| 插件 | 用途 |
|------|------|
| **Graph View** | 可视化条目间的链接关系 |
| **Dataview** | 查询 frontmatter 元数据（如 `confidence: high`） |
| **Web Clipper** | 将网页转为 Markdown，直接摄入 sources |
| **Templates** | 标准化条目格式 |

**其他工具：**
- **Git**: Wiki 即 Markdown 文件的 Git 仓库 — 版本历史、分支、协作
- **Marp**: 从 Wiki 内容生成幻灯片
- **图片**: 下载到本地附件目录，确保长期可访问

## 目录结构

```
~/wiki/
├── sources/                          # 原始素材（不可变）
│   └── 2024-04-12-注意力机制概述.md
├── wiki/                            # AI 合成 Wiki 条目（按分类组织）
│   ├── 研究/
│   │   ├── 2024-03-15-注意力机制.md
│   │   └── 2024-03-10-transformer架构.md
│   ├── 成长/
│   │   └── 2024-03-01-习惯养成.md
│   └── 学习/
│       └── 2024-01-15-机器学习基础.md
├── schema.md                        # 行为规范
└── .obsidian/                       # Obsidian 配置（可选）
```

**Wiki 条目命名：**
- 文件名：`YYYY-MM-DD-标题.md`
- 条目间通过 `[[YYYY-MM-DD-标题]]` 相互链接
- 分类由 AI 在 Ingest 时分析内容主题自动确定
