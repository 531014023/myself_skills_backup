"""
知识库列出 collections 脚本
用法: python scripts/list_collections.py
"""
import sys
import json
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
    rag_cfg = config.get("rag_kb", {})
    api_url = rag_cfg.get("api_url", "http://localhost:8081")

    try:
        import requests
        resp = requests.get(f"{api_url}/collections", timeout=30)
        resp.raise_for_status()
        result = resp.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()