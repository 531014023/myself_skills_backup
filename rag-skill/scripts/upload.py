"""
知识库上传文件脚本
用法: python scripts/upload.py <file_path> [-c collection]
"""
import sys
import json
import argparse
from pathlib import Path

import yaml
import requests


def find_config():
    skill_dir = Path(__file__).parent.parent
    cfg_path = skill_dir / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


config = find_config()


def main():
    parser = argparse.ArgumentParser(description="RAG KB 上传文件")
    parser.add_argument("file", help="文件路径")
    parser.add_argument("-c", "--collection", default=config.get("default_collection", "default"))
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在: {args.file}")
        sys.exit(1)

    rag_cfg = config.get("rag_kb", {})
    api_url = rag_cfg.get("api_url", "http://localhost:8081")

    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{api_url}/upload",
                files={"file": (file_path.name, f)},
                data={"collection": args.collection},
                timeout=120
            )
        resp.raise_for_status()
        result = resp.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except requests.HTTPError as e:
        try:
            err = e.response.json()
            print(f"错误: {err.get('detail', e)}")
        except:
            print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()