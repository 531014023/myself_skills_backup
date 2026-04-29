"""
知识库上传文件夹脚本
用法: python scripts/upload_folder.py <folder_path> [-c collection]
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


# 支持的文件扩展名（与 MarkItDown 支持的格式一致）
SUPPORTED_EXTENSIONS = [
    ".pdf", ".pptx", ".ppt", ".docx", ".doc",
    ".xlsx", ".xls",
    ".md", ".txt",
    ".html", ".htm", ".epub",
    ".csv", ".json", ".xml", ".zip"
]


def is_supported(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def main():
    parser = argparse.ArgumentParser(description="RAG KB 上传文件夹")
    parser.add_argument("folder", help="文件夹路径")
    parser.add_argument("-c", "--collection", default=config.get("default_collection", "default"))
    args = parser.parse_args()

    folder_path = Path(args.folder)
    if not folder_path.is_dir():
        print(f"错误: 不是有效的目录: {args.folder}")
        sys.exit(1)

    # 收集所有支持的文件
    files = [f for f in folder_path.rglob("*") if f.is_file() and is_supported(f)]

    if not files:
        print(f"错误: 目录中没有找到支持的文件")
        sys.exit(1)

    rag_cfg = config.get("rag_kb", {})
    api_url = rag_cfg.get("api_url", "http://localhost:8081")

    # 逐个上传文件
    results = []
    for file_path in files:
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
            results.append({"file": str(file_path), "success": True, "result": result})
        except Exception as e:
            results.append({"file": str(file_path), "success": False, "error": str(e)})

    # 输出汇总
    success_count = sum(1 for r in results if r["success"])
    print(json.dumps({
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()