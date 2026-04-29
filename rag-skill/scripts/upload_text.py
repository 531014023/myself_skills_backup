"""
知识库上传文本脚本
用法: python scripts/upload_text.py "文本内容" [-c collection] [-s source]
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
    parser = argparse.ArgumentParser(description="RAG KB 上传文本")
    parser.add_argument("text", help="文本内容")
    parser.add_argument("-c", "--collection", default=config.get("default_collection", "default"))
    parser.add_argument("-s", "--source", default="cli")
    args = parser.parse_args()

    rag_cfg = config.get("rag_kb", {})
    api_url = rag_cfg.get("api_url", "http://localhost:8081")

    try:
        import requests
        resp = requests.post(
            f"{api_url}/upload-text",
            json={"text": args.text, "collection": args.collection, "source": args.source},
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