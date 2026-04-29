---
name: rag-skill
description: |
  RAG 知识库管理 Skill。当用户说以下内容时触发：
  - "上传到知识库"、"知识库上传"、"上传文档"
  - "搜索知识库"、"知识库检索"、"检索"
  - "删除知识库"、"知识库删除"
  - "列出知识库"、"查看知识库"

  用途：通过 CLI 脚本连接 rag-kb API 进行知识库操作。
version: 1.0.0
---

# RAG Knowledge Base Skill

通过 CLI 脚本连接 rag-kb API 服务的 Skill。

## 配置

在 skill 目录下创建 `config.yaml`：

```yaml
rag_kb:
  api_url: "http://localhost:8081"  # rag-kb API 服务地址
```

## CLI 脚本

| 脚本 | 用法 | 说明 |
|------|------|------|
| `python scripts/search.py "查询" [-c collection] [-k top_k]` | 检索 |
| `python scripts/upload.py <file> [-c collection]` | 上传文件 |
| `python scripts/upload_folder.py <folder> [-c collection]` | 上传文件夹（支持 pdf, docx, xlsx, pptx, html, md, txt, epub, csv, json, xml, zip 等） |
| `python scripts/upload_text.py "文本" [-c collection]` | 上传文本 |
| `python scripts/delete.py <doc_id> [-c collection]` | 删除文档 |
| `python scripts/list_collections.py` | 列出 collection |

## 使用示例

```bash
# 检索
python scripts/search.py "什么是安全边际" -c 投资 -k 5

# 上传文件
python scripts/upload.py ./docs/article.md -c 投资

# 上传文件夹
python scripts/upload_folder.py ./docs/ -c 投资

# 上传文本
python scripts/upload_text.py "巴菲特的投资理念..." -c 投资

# 删除
python scripts/delete.py doc_id_abc123 -c 投资

# 列出
python scripts/list_collections.py
```

## 返回格式

脚本输出 JSON 格式结果：
- `success`: bool，操作是否成功
- `results`: list[dict]，检索结果
- `message`: str，描述信息

## 触发场景

- 用户请求上传、检索、删除、列出知识库时
- 上传文件夹或多文件时
- Agent 需要访问知识库内容时