---
name: llm-wiki
description: LLM Wiki 个人知识库管理。支持：1）初始化新知识库；2）操作已有知识库（通过config.yaml配置多知识库）。当提到「初始化 wiki、创建 wiki 项目、新建知识库、添加知识库、注册知识库」时触发。
---

# LLM Wiki - 个人知识库

## ⚠️ 边界声明

**触发词：**
- 初始化类：初始化 wiki、创建 wiki 项目、新建知识库、添加知识库、注册知识库
- 操作类：存到 wiki、整理到知识库、做个摘要、维基体检

**操作拦截：**
如果用户尝试执行 ingest/query/lint 等日常操作：
1. 读取 `{skill-root}/config.yaml` 获取知识库列表
2. 如果有多个知识库 → 展示列表让用户选择
3. 用户选择后 → cd 到对应目录
4. 加载该知识库的 schema 文件（由初始化时指定，如 `CLAUDE.md` 或 `AGENTS.md`）→ 执行对应操作

---

## 配置文件

**路径：** 与 SKILL.md 同目录下的 `config.yaml`

**格式：**
```yaml
knowledge_bases:
  - name: 主知识库
    path: ~/wiki
    schema: CLAUDE.md
  - name: 投资库
    path: ~/invest-wiki
    schema: AGENTS.md
```

---

## 核心操作

### 1. 初始化新知识库

**触发词：** 初始化 wiki、创建 wiki 项目、新建知识库

**Step 1. 询问项目信息**
- 知识库名称（作为外层目录名）
- 创建位置（默认 `~/wiki`）
- Schema 文件名：
  - Claude Code → `CLAUDE.md`
  - 通用/其他 Agent → `AGENTS.md`
  - 或自定义名称

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
├── index.md                          # 内容索引
└── log.md                            # 操作日志
```

**Step 3. 复制 schema-template.md 为用户指定的 schema 文件名**
将 `references/schema-template.md` 复制到目标目录，命名为用户选择的 schema 文件名

**Step 4. 注册到 config.yaml**
将新知识库追加到 `{skill-root}/config.yaml`，包含 name、path 和 schema 文件名

**Step 5. 初始化完成**
- 确认目录结构已创建
- 告知用户后续操作

---

### 2. 操作已有知识库

**入口：** 用户说"切换到投资库"、"操作主知识库"、或执行 ingest/query/lint 等日常操作

**Step 1. 读取配置文件**
读取 `{skill-root}/config.yaml`，解析知识库列表

**Step 2. 展示知识库列表**
如果有多条知识库，展示选择菜单：
```
可用知识库：
1. 主知识库 (~/wiki)
2. 投资库 (~/invest-wiki)
请选择操作的知识库：
```

**Step 3. 用户选择后**
- `cd` 到对应目录
- 加载该知识库的 schema 文件（如 `CLAUDE.md` 或 `AGENTS.md`）

**Step 4. 加载 schema 文件执行操作**
后续操作遵循该 schema 文件中的规范执行

---

### 3. 配置知识库

**触发词：** 添加知识库、注册知识库、切换知识库

**执行步骤：**
1. 询问知识库名称和路径
2. 更新 `{skill-root}/config.yaml`（追加新知识库）
3. 确认完成
