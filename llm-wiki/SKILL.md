---
name: llm-wiki
description: 初始化 LLM Wiki 个人知识库项目。当提到「初始化 wiki、创建 wiki 项目、新建知识库」时触发。
---

# LLM Wiki - 个人知识库初始化

## ⚠️ 边界声明

**触发词：** 初始化 wiki、创建 wiki 项目、新建知识库

**操作拦截：**
如果用户尝试执行 ingest/query/lint 等日常操作 → 提示：
「请切换到知识库目录，直接加载 CLAUDE.md 执行操作」

---

## 初始化流程

**Step 1. 询问项目信息**
- 知识库名称（作为外层目录名）
- 创建位置（默认 `~/wiki`）

**Step 2. 创建项目目录结构**
```
knowledge-base-name/
├── raw/                              # 原始素材（不可变）
├── wiki/
│   ├── 摘要/                         # 单篇文章摘要
│   ├── 实体/                         # 人、公司、产品
│   ├── 概念/                         # 抽象概念、方法论
│   ├── 对比/                         # 多方案对比分析
│   ├── 概览/                         # 主题/体系概览
│   └── 综合/                         # 跨领域综合
├── CLAUDE.md                         # 项目行为规范
├── index.md                          # 内容索引
└── log.md                            # 操作日志
```

**Step 3. 复制 schema-template.md 为 CLAUDE.md**
将 `references/schema-template.md` 复制到目标目录作为 `CLAUDE.md`

**Step 4. 初始化完成**
- 确认目录结构已创建
- 告知用户后续操作：切换到知识库目录，直接加载 `CLAUDE.md` 执行 ingest/query/lint
