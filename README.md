# Claude Skills 技能库

> 本目录包含 32 个 Claude Code 技能（Skills），覆盖投资研究、文档处理、思维框架、信息搜索等多个领域。

---

## 目录

### 一、价值投资思维框架（8个）

| Skill | 名称 | 描述 |
|-------|------|------|
| [buffett-perspective](./buffett-perspective) | 巴菲特视角 | 沃伦·巴菲特的思维框架与表达方式。基于600万字原典资料，提炼5个核心心智模型、10条决策启发式。激活词：巴菲特视角/Buffett perspective/苹果/可口可乐分析 |
| [munger-perspective](./munger-perspective) | 芒格视角 | 查理·芒格的思维框架。基于《穷查理宝典》等120+来源，提炼6个核心心智模型、14条决策启发式。擅长逆向思考、Lollapalooza效应、激励诊断 |
| [tang-chao-perspective](./tang-chao-perspective) | 唐朝视角 | 唐朝（老唐）的价值投资思维框架。基于246万字文集，提炼5个核心心智模型、"至简三板斧"估值法、中翻中式表达 |
| [duanyongping-perspective](./duanyongping-perspective) | 段永平视角 | 段永平（大道）的思维框架。提炼5个核心心智模型、10条决策启发式。擅长：本分、平常心、能力圈、"买股票就是买公司" |
| [feynman-perspective](./feynman-perspective) | 费曼视角 | 理查德·费曼的思维框架。擅长：检验是否真正理解（vs记住名字）、识别货物崇拜、反自欺、具象化思考 |
| [book-multi-lens](./book-multi-lens) | 书籍辩论 | 当用户分享书籍/人物观点时，启动两位辩手从不同视角深度辩论，帮助用户从"中道"立场全面理解观点 |
| [value-investment-debate](./value-investment-debate) | 价值投资辩论 | 多角色（巴菲特+芒格+唐朝等）多角度辩论分析投资标的。数据优先，多轮交锋，评分总结 |
| [personal-writing-style](./personal-writing-style) | 投资写作风格 | 第一人称叙事、结构化逻辑分析、数据驱动、直接坦率的语言表达和深度反思思维模式 |

### 二、股票研究工具（3个）

| Skill | 名称 | 描述 |
|-------|------|------|
| [stock-research-engine](./stock-research-engine) | 个股研究引擎 | 买方基金经理视角的个股深度研究。覆盖A股/港股/美股，输出投资分析简报（含市场情绪、基本面、管理层、估值等） |
| [cninfo-annual-download](./cninfo-annual-download) | 年报下载器 | 巨潮资讯网年报下载器。支持A股（沪/深/北交所）和港股的年报、半年报、季报等定期报告下载 |
| [annual-report-extractor](./annual-report-extractor) | 年报数据提取 | 从年报PDF中提取数值型财务数据和产能数据。支持任意字段自动适配，输出CSV格式 |

### 三、文档处理（6个）

| Skill | 名称 | 描述 |
|-------|------|------|
| [pdf](./pdf) | PDF处理 | PDF文件处理全功能：读取文本/表格、合并/拆分、旋转、添加水印、创建PDF、OCR识别等 |
| [docx](./docx) | Word文档 | Word文档创建、编辑、格式处理。支持tracked changes、comments、模板编辑、XML操作 |
| [xlsx](./xlsx) | Excel处理 | Excel文件处理：数据分析和pandas操作、公式和格式化、财务模型规范（颜色编码、公式错误零容忍） |
| [pptx](./pptx) | PowerPoint | PowerPoint演示文稿：读取内容、模板编辑、从零创建、视觉设计指南 |
| [pptx-generator](./pptx-generator) | PPT生成器 | 使用PptxGenJS从零创建PPT。包含完整设计系统（配色、字体、样式配方）和5种页面类型 |
| [epub](./epub) | EPUB处理 | EPUB电子书处理：将epub当作ZIP解压提取内容、解析导航文件、提取元数据和目录 |

### 四、信息搜索（5个）

| Skill | 名称 | 描述 |
|-------|------|------|
| [多引擎搜索](./多引擎搜索) | 多引擎搜索 | 集成17个搜索引擎（8国内+9国际）：百度/Bing/Google/DuckDuckGo等，支持高级搜索运算符、时间过滤 |
| [smart-web-fetch](./smart-web-fetch) | 智能网页抓取 | 替代web_fetch，自动使用Jina Reader/markdown.new/defuddle.md清洗服务获取干净Markdown，节省50-80% Token |
| [hotlist-fetcher](./hotlist-fetcher) | 热榜抓取 | 自动抓取tophub.today热榜数据，整理成结构化Markdown文档（含平台统计、热点分类、选题建议） |
| [wechat-article-search](./wechat-article-search) | 微信文章搜索 | 搜索微信公众号文章，返回标题、摘要、发布时间、来源公众号和链接 |
| [find-skills](./find-skills) | 技能发现 | 从开放agent技能生态系统中发现和安装技能 |

### 五、思维与工作流（5个）

| Skill | 名称 | 描述 |
|-------|------|------|
| [huashu-nuwa](./huashu-nuwa) | 女娲造人 | 输入人名/主题/模糊需求，自动深度调研→思维框架提炼→生成可运行的人物Skill。支持从零创建或更新已有Skill |
| [personal-rules](./personal-rules) | 专家回答框架 | 全域双轨专家级回答框架。强制要求：权威学术/官方信源、实时验证信息、多学科视角、多声部争议呈现 |
| [opinion-analyzer](./opinion-analyzer) | 舆情分析 | 多视角舆情分析助手。模拟Query/Insight/Forum/Report四个Agent，还原舆情原貌、打破信息茧房 |
| [pua](./pua) | PUA激励引擎 | 用大厂PUA话术穷尽一切方案。让AI不敢摆烂，适用于任务失败2+次或反复微调同一思路 |
| [self-improving-agent](./self-improving-agent) | 自我改进 | 捕获学习、错误和纠正，实现持续改进。记录到.learnings/目录，重要内容升级到项目内存 |

### 六、知识管理与工具（5个）

| Skill | 名称 | 描述 |
|-------|------|------|
| [ima-skill](./ima-skill) | IMA笔记 | 统一的IMA OpenAPI技能，支持笔记管理和知识库操作。上传文件、添加网页、搜索知识库、笔记CRUD |
| [obsidian](./obsidian) | Obsidian操作 | 通过obsidian-cli操作Obsidian vaults。搜索笔记、创建笔记、移动/重命名、删除 |
| [humanize-chinese](./humanize-chinese) | 去AI味 | 检测和改写中文AI生成文本。20+检测维度、7种风格转换、学术论文AIGC降重 |
| [skill-creator](./skill-creator) | 技能创建指南 | 创建有效Skills的指南。包含目录结构、最佳实践、脚本/references/assets组织方式 |
| [skill-vetter-1.0.0](./skill-vetter-1.0.0) | 技能安全审查 | AI agent技能的安全审查协议。安装前检查红标、权限范围、可疑模式 |

---

## 快速导航

**投资研究**：想分析某只股票？→ [stock-research-engine](./stock-research-engine) + [value-investment-debate](./value-investment-debate)

**年报数据**：需要下载和提取年报数据？→ [cninfo-annual-download](./cninfo-annual-download) + [annual-report-extractor](./annual-report-extractor)

**思维框架**：需要从伟人视角分析问题？→ [buffett-perspective](./buffett-perspective) / [munger-perspective](./munger-perspective) / [tang-chao-perspective](./tang-chao-perspective) / [feynman-perspective](./feynman-perspective)

**文档处理**：需要处理PDF/Word/Excel/PPT？→ [pdf](./pdf) / [docx](./docx) / [xlsx](./xlsx) / [pptx](./pptx)

**信息搜索**：需要搜索和抓取网络内容？→ [多引擎搜索](./多引擎搜索) / [smart-web-fetch](./smart-web-fetch) / [hotlist-fetcher](./hotlist-fetcher)

**创建新技能**：需要构建新的人物思维框架？→ [huashu-nuwa](./huashu-nuwa)

---

*最后更新：2026-04-11*
