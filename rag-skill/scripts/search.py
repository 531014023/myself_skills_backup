"""
知识库检索脚本
用法: python scripts/search.py "查询内容" [-c collection] [-k top_k]
"""
import sys
import json
import argparse
from pathlib import Path

import yaml


def find_config():
    """从 skill 目录读取 config.yaml"""
    skill_dir = Path(__file__).parent.parent
    cfg_path = skill_dir / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


config = find_config()


def main():
    parser = argparse.ArgumentParser(description="RAG KB 检索")
    parser.add_argument("query", help="检索查询")
    parser.add_argument("-c", "--collection", default=config.get("default_collection", "default"))
    parser.add_argument("-k", "--top-k", type=int, default=config.get("default_top_k", 5))
    args = parser.parse_args()

    rag_cfg = config.get("rag_kb", {})
    api_url = rag_cfg.get("api_url", "http://localhost:8081")

    try:
        import requests
        resp = requests.post(
            f"{api_url}/search",
            json={"query": args.query, "collection": args.collection, "top_k": args.top_k},
            timeout=60
        )
        resp.raise_for_status()
        result = resp.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()