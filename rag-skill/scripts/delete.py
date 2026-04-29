"""
知识库删除文档脚本
用法: python scripts/delete.py <doc_id> [-c collection]
"""
import sys
import json
import argparse
from pathlib import Path

import yaml


def find_config():
    skill_dir = Path(__file__).parent.parent
    cfg_path = skill_dir / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


config = find_config()


def main():
    parser = argparse.ArgumentParser(description="RAG KB 删除文档")
    parser.add_argument("doc_id", help="文档 ID")
    parser.add_argument("-c", "--collection", default=config.get("default_collection", "default"))
    args = parser.parse_args()

    rag_cfg = config.get("rag_kb", {})
    api_url = rag_cfg.get("api_url", "http://localhost:8081")

    try:
        import requests
        resp = requests.post(
            f"{api_url}/delete",
            json={"doc_id": args.doc_id, "collection": args.collection},
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